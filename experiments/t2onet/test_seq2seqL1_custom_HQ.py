import os
import time
import pdb
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

import utils.html as html
from utils.visualize import update_web
from options.seq2seqGAN_train_options import TrainOptions
from datasets.FiveKdataset import FiveK
from datasets.Customdataset import CustomDatasetHQ
from models.actor import Actor
from PIL import Image
from utils.eval import ImageEvaluator
from utils.text_utils import load_vocab, txt2idx
import numpy as np
from torchvision.utils import save_image


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def concatenate_horizontally_pil(images, padding_size=0, padding_color=(255, 255, 255)):
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths) + padding_size * (len(images) - 1)
    max_height = max(heights)

    new_img = Image.new("RGB", (total_width, max_height), color=padding_color)

    x_offset = 0
    for img in images:
        new_img.paste(img, (x_offset, 0))
        x_offset += img.width + padding_size
    
    return new_img

def set_web(opt):
    web_dir = os.path.join(opt.run_dir, 'test', 'web')
    img_dir = os.path.join(web_dir, 'images')
    webpage = html.HTML(web_dir, 'inference result', reflesh=1)
    webpage.add_header('Visualization of  result for trial {}'.format(opt.trial))
    return webpage, img_dir


def test(model, loader, opt, is_test=False):
    """train model"""
    model.eval()
    itr = 0
    avg_time = 0
    avg_dist = 0
    avg_init_dist = 0

    # save web
    if opt.visualize:
        webpage, img_dir = set_web(opt)

    # eval
    if is_test:
        Eval = ImageEvaluator()

    # make model
    if hasattr(model, 'module'):
        single_model = model.module
    else:
        single_model = model

    for i, data in enumerate(loader):
        # for i in range(1000):
        itr += 1
        tik = time.time()
        img_x, txt = data
        # ship to device
        img_x = img_x.to(device)
        vocab2id, _, _, _ = load_vocab(opt.vocab_dir, opt.dataset, opt.session)
        x = txt2idx(txt[0], vocab2id, opt.encoder_max_len).to(device)
        with torch.no_grad():
            state, pred_imgs, pred_ops, pred_params = model.episode_forward(x, img_x, mask_dict=None,
                                                                                        reinforce_sample=False)
        # for loop to get column index with end token
        end_fake_imgs = []
        bs, max_len, cn, h, w = pred_imgs.shape
        for bs_i in range(bs):
            idxs = (pred_ops[bs_i] == opt.end_id).nonzero()
            col_idx = idxs[0][0] if len(idxs) > 0 else max_len - 1
            end_fake_imgs.append(pred_imgs[bs_i, col_idx])
        pred_img = torch.stack(end_fake_imgs)

        results_folder = f"results_HQ/{i:03d}"
        os.makedirs(results_folder, exist_ok=True)
        
        img_x = img_x[0].permute(1, 2, 0).cpu().numpy()*255
        pred_img = pred_img[0].permute(1, 2, 0).cpu().numpy()*255
        
        img_x = Image.fromarray(img_x.astype(np.uint8)).resize((512, 512))
        pred_img = Image.fromarray(pred_img.astype(np.uint8)).resize((512, 512))
        img_x.save(os.path.join(results_folder, "input.jpg"))
        pred_img.save(os.path.join(results_folder, "pred.jpg"))
        
        concatenated_image = concatenate_horizontally_pil([img_x, pred_img], padding_size=10)
        concatenated_image.save(os.path.join(results_folder, "concatenated_image.jpg"))
        
        # save_image(torch.nn.functional.interpolate(img_x, (512, 512))[0], os.path.join(results_folder, "input.jpg"))
        # save_image(torch.nn.functional.interpolate(img_y, (512, 512))[0], os.path.join(results_folder, "target.jpg"))
        # save_image(torch.nn.functional.interpolate(pred_img, (512, 512))[0], os.path.join(results_folder, "pred.jpg"))
        
        # tok = time.time()
        # avg_time = avg_time * (1 - 1/itr) + (tok - tik) / itr
        # init_dist = torch.abs(img_x - img_y).mean().item()
        # dist = torch.abs(pred_img - img_y).mean().item()
        # avg_init_dist = avg_init_dist * (1 - 1/itr) + init_dist/itr
        # avg_dist = avg_dist * (1 - 1 / itr) + dist / itr

        # if is_test:
        #     Eval.update(img_x, pred_img, img_y)

        # if itr % opt.print_every == 0:
        #     print('iter {:6d} / {}, init dist {:.2f},  L1 dist {:.2f} time {:.2f}'.format(itr, len(loader), init_dist, dist, avg_time))

        # if opt.visualize and itr % opt.visualize_every == 0:
        #     pred_params = torch.cat([pred_params[i][:, :1] for i in range(len(pred_params))]).unsqueeze(0)
        #     pdb.set_trace()
    
    # if opt.visualize:
    #         update_web(webpage, req, None, img_x.cpu().numpy(), img_y.unsqueeze(0).cpu().numpy(), pred_imgs.cpu().numpy(), None, pred_params.cpu().numpy(), itr, pred_ops.cpu().numpy(), loader.dataset.id2op_vocab, img_dir, supervise=0)

    # if opt.visualize:
    #     webpage.save()

    # if is_test:
    #     Eval.eval()

    print('inference init L1 dist {:.4f}; L1 dist {:.4f}'.format(avg_init_dist, avg_dist))
    return avg_init_dist, avg_dist



def test_variance(model, loader, opt):
    model.eval()
    itr = 0
    # load and preprocessing img and text
    from core.utils.eval import test_txts

    vocab2id, _, _, _ = load_vocab(opt.vocab_dir, opt.dataset, opt.session)

    avg_time, avg_var = 0, 0
    for i, data in enumerate(loader):
        # for i in range(1000):
        itr += 1
        tik = time.time()
        img_x, img_y, x, req = data
        # ship to device
        x, img_x, img_y = list(map(lambda r: r.to(device), [x, img_x, img_y]))
        pred_img_lst = []
        for txt in test_txts:
            x = txt2idx(txt, vocab2id, opt.encoder_max_len).to(device)
            with torch.no_grad():
                state, pred_imgs, pred_ops, pred_params = model.episode_forward(x, img_x, mask_dict=None,
                                                                                reinforce_sample=False)
            # for loop to get column index with end token
            end_fake_imgs = []
            bs, max_len, cn, h, w = pred_imgs.shape
            for bs_i in range(bs):
                idxs = (pred_ops[bs_i] == opt.end_id).nonzero()
                col_idx = idxs[0][0] if len(idxs) > 0 else max_len - 1
                end_fake_imgs.append(pred_imgs[bs_i, col_idx])
            pred_img = torch.stack(end_fake_imgs)
            pred_img_lst.append(pred_img)
        pred_imgs = torch.cat(pred_img_lst)
        _, cn, _, _ = pred_imgs.shape
        var = torch.var(pred_imgs, dim=0)
        avg_var = avg_var * (1 - 1/itr) + var.mean().item()/itr

        tok = time.time()
        avg_time = avg_time * (1 - 1/itr) + (tok - tik) / itr

        if itr % opt.print_every == 0:
            print('iter {:6d} / {}, var {:.6f}, time {:.2f}'.format(itr, len(loader), avg_var, avg_time))

    print('avg var: {:.6f}'.format(avg_var))
    return avg_var


if __name__ == '__main__':
    # options
    opt = TrainOptions().parse()

    # data loader
    img_dir = 'data/FiveK/images'
    anno_dir = 'data/FiveK/annotations'
    test_dataset = CustomDatasetHQ()
    loader = DataLoader(test_dataset, batch_size=opt.batch_size, shuffle=False, num_workers=opt.num_workers)
    # load model
    model = Actor(opt)
    ckpt_dir = os.path.join(opt.run_dir, 'seq2seqL1_model')
    model_dir = os.path.join(ckpt_dir, 'checkpoint_best')
    model.load_state_dict(torch.load(os.path.join(model_dir, 'model.pth')), strict=False)
    print('loaded model from {}'.format(model_dir))
    model.cuda()

    # test
    test(model, loader, opt, is_test=True)
    # test_variance(model, loader, opt)
