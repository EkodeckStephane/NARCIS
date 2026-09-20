from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
import argparse, io, json, random, hashlib
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image, ImageOps, ImageFilter
import torchvision.transforms.functional as TF

IMAGE_SUFFIXES={'.png','.jpg','.jpeg','.bmp','.pgm','.tif','.tiff'}
def discover_images(root): return sorted(p for p in Path(root).rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
def sha256_file(path):
 h=hashlib.sha256(); f=open(path,'rb')
 for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 f.close(); return h.hexdigest()
class ConvBlock(nn.Sequential):
 def __init__(self,i,o,stride=1): super().__init__(nn.Conv2d(i,o,3,stride=stride,padding=1,bias=False),nn.BatchNorm2d(o),nn.SiLU(inplace=True),nn.Conv2d(o,o,3,padding=1,bias=False),nn.BatchNorm2d(o),nn.SiLU(inplace=True))
class RobustImageEncoder(nn.Module):
 def __init__(self,embedding_dim=64,base_channels=16,in_channels=3):
  super().__init__(); c=base_channels
  self.backbone=nn.Sequential(ConvBlock(in_channels,c),ConvBlock(c,2*c,2),ConvBlock(2*c,4*c,2),ConvBlock(4*c,6*c,2),nn.AdaptiveAvgPool2d(1))
  self.projector=nn.Sequential(nn.Flatten(),nn.Linear(6*c,2*embedding_dim),nn.SiLU(inplace=True),nn.Linear(2*embedding_dim,embedding_dim))
 def forward(self,x): return F.normalize(self.projector(self.backbone(x)),dim=1)
class ChannelAugment:
 def __init__(self,image_size,seed=None): self.image_size=image_size; self.random=random.Random(seed)
 def __call__(self,t):
  image=TF.to_pil_image(t); op=self.random.choice(('jpeg','noise','blur','resize','crop','rotate','identity'))
  if op=='jpeg':
   b=io.BytesIO(); image.save(b,format='JPEG',quality=self.random.randint(55,90)); b.seek(0); image=Image.open(b).convert(image.mode)
  elif op=='noise':
   a=np.asarray(image,dtype=np.float32); sigma=self.random.uniform(2.,15.); noise=np.random.default_rng(self.random.randrange(2**32)).normal(0.,sigma,a.shape); image=Image.fromarray(np.clip(a+noise,0,255).astype(np.uint8))
  elif op=='blur': image=image.filter(ImageFilter.GaussianBlur(radius=self.random.uniform(.3,1.8)))
  elif op=='resize':
   s=self.random.uniform(.65,.95); side=max(16,int(self.image_size*s)); image=image.resize((side,side),Image.Resampling.BILINEAR)
  elif op=='crop':
   m=self.random.randint(2,max(2,self.image_size//10)); image=image.crop((m,m,image.width-m,image.height-m))
  elif op=='rotate': image=image.rotate(self.random.uniform(-8.,8.),resample=Image.Resampling.BILINEAR,fillcolor=(0,0,0))
  image=image.resize((self.image_size,self.image_size),Image.Resampling.BICUBIC); return TF.to_tensor(image)
@dataclass(frozen=True)
class Cfg: invariance_weight:float=25.; variance_weight:float=25.; covariance_weight:float=1.
def offdiag(m): n=m.shape[0]; return m.flatten()[:-1].view(n-1,n+1)[:,1:].flatten()
def lossfn(a,b,cfg):
 inv=F.mse_loss(a,b); eps=1e-4; target=a.shape[1]**-0.5; sa=torch.sqrt(a.var(dim=0)+eps); sb=torch.sqrt(b.var(dim=0)+eps); var=F.relu(target-sa).mean()+F.relu(target-sb).mean(); ac=a-a.mean(0); bc=b-b.mean(0); d=max(1,a.shape[0]-1); cov=offdiag(ac.T@ac/d).pow(2).mean()+offdiag(bc.T@bc/d).pow(2).mean(); total=25*inv+25*var+cov; return total,{'loss':float(total.detach()),'invariance':float(inv.detach()),'variance':float(var.detach()),'covariance':float(cov.detach())}
def model_view(x): return F.interpolate(x,size=(128,128),mode='bicubic',align_corners=False,antialias=True)
class CacheDS(Dataset):
 def __init__(self,path): self.a=np.load(path,mmap_mode='r')
 def __len__(self): return len(self.a)
 def __getitem__(self,i): return torch.from_numpy(self.a[i].astype(np.float32)/np.float32(255.0)), i
def build_cache(paths,path):
 if path.exists(): return
 a=np.lib.format.open_memmap(path,mode='w+',dtype=np.uint8,shape=(len(paths),3,256,256))
 for i,p in enumerate(paths):
  im=ImageOps.fit(Image.open(p).convert('RGB'),(256,256),method=Image.Resampling.BICUBIC); a[i]=np.asarray(im,dtype=np.uint8).transpose(2,0,1)
 a.flush()
def validate_cache(paths,path):
 a=np.load(path,mmap_mode='r')
 for i in np.linspace(0,len(paths)-1,16,dtype=int):
  im=ImageOps.fit(Image.open(paths[i]).convert('RGB'),(256,256),method=Image.Resampling.BICUBIC); direct=(np.asarray(im,dtype=np.float32)/255.0).transpose(2,0,1); cached=a[i].astype(np.float32)/np.float32(255.0)
  if not np.array_equal(direct,cached): raise RuntimeError(f'cache mismatch {i}')
def state_save(path,payload):
 tmp=path.with_suffix('.tmp'); torch.save(payload,tmp); tmp.replace(path)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,required=True); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--max-batches',type=int,default=25); args=ap.parse_args()
 torch.set_num_threads(1); torch.set_num_interop_threads(1); seed=args.seed; out=args.out; out.mkdir(parents=True,exist_ok=True)
 paths=discover_images(args.root); order=np.random.default_rng(seed).permutation(len(paths)); train=[paths[i] for i in order[:1500]]; cache=out/f'train_cache_seed_{seed}.npy'; build_cache(train,cache); validate_cache(train,cache); (out/f'train_files_seed_{seed}.txt').write_text('\n'.join(str(p) for p in train)+'\n')
 random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); model=RobustImageEncoder(); ds=CacheDS(cache); loader=DataLoader(ds,batch_size=16,shuffle=True,drop_last=True); aug=ChannelAugment(128,seed); opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-5); cfg=Cfg()
 statep=out/f'training_state_seed_{seed}.pt'; history=[]; completed=0; plan=None; pos=0; totals=Counter(); batches_done=0
 if statep.exists():
  st=torch.load(statep,map_location='cpu',weights_only=False); completed=st['completed_epoch']; history=st['history']; model.load_state_dict(st['model_state']); opt.load_state_dict(st['optimizer_state']); torch.set_rng_state(st['torch_rng_state']); np.random.set_state(st['numpy_rng_state']); random.setstate(st['python_rng_state']); aug.random.setstate(st['augment_rng_state']); plan=st.get('batch_plan'); pos=st.get('batch_pos',0); totals=Counter(st.get('totals',{})); batches_done=st.get('batches_done',0)
 if completed>=5:
  final=out/f'encoder_seed_{seed}.pt';
  if not final.exists(): torch.save(model.state_dict(),final)
  print(json.dumps({'seed':seed,'completed_epoch':completed,'final_sha256':sha256_file(final),'status':'complete'})); return
 if plan is None:
  it=iter(loader); plan=[list(map(int,b)) for b in list(it._sampler_iter)]; pos=0; totals=Counter(); batches_done=0
 model.train(); end=min(len(plan),pos+args.max_batches); arr=np.load(cache,mmap_mode='r')
 for j in range(pos,end):
  idx=plan[j]; native=torch.from_numpy(arr[idx].astype(np.float32)/np.float32(255.0)); resized=model_view(native); first=torch.stack([aug(x) for x in resized]); second=torch.stack([aug(x) for x in resized]); opt.zero_grad(set_to_none=True); loss,m=lossfn(model(first),model(second),cfg); loss.backward(); opt.step(); totals.update(m); batches_done+=1
 pos=end; epoch_finished=pos>=len(plan)
 if epoch_finished:
  row={'seed':seed,'epoch':completed+1,**{k:v/batches_done for k,v in totals.items()}}; history.append(row); completed+=1; plan=None; pos=0; totals=Counter(); batches_done=0
 payload={'seed':seed,'completed_epoch':completed,'model_state':model.state_dict(),'optimizer_state':opt.state_dict(),'torch_rng_state':torch.get_rng_state(),'numpy_rng_state':np.random.get_state(),'python_rng_state':random.getstate(),'augment_rng_state':aug.random.getstate(),'history':history,'batch_plan':plan,'batch_pos':pos,'totals':dict(totals),'batches_done':batches_done,'threads':torch.get_num_threads()}; state_save(statep,payload)
 result={'seed':seed,'completed_epoch':completed,'epoch_finished':epoch_finished,'batch_pos':pos,'plan_len':len(plan) if plan is not None else None,'history':history,'state_sha256':sha256_file(statep)}
 if completed>=5:
  final=out/f'encoder_seed_{seed}.pt'; torch.save(model.state_dict(),final); result['final_sha256']=sha256_file(final)
 (out/f'status_seed_{seed}.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
