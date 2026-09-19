from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import hashlib,hmac,math
from typing import Iterable,Sequence
import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .protocol import keyed_permutation

PAYLOAD_ID=b'NARCIS-PAYLOAD-1'; VERSION='ARCIS-PERM-RRNS-1'; K=8; G=5; R=18
CANDIDATES=4; BEAM_WIDTH=600; BEAM_POSITIONS=12

def subkey(k,l): return hmac.new(k,l,hashlib.sha256).digest()
def nonce(k,s):
    if not 0<=s<2**64: raise ValueError('sequence must fit uint64')
    return subkey(k,b'nonce-prefix')[:4]+s.to_bytes(8,'big')
def protect(p,k,s):
    n=nonce(k,s); a=PAYLOAD_ID+s.to_bytes(8,'big')
    return AESGCM(subkey(k,b'payload-encryption')).encrypt(n,p,a)
def unprotect(c,k,s):
    n=nonce(k,s); a=PAYLOAD_ID+s.to_bytes(8,'big')
    return AESGCM(subkey(k,b'payload-encryption')).decrypt(n,c,a)

def mr_unrank(n,r):
    if r<0 or r>=math.factorial(n): raise ValueError('rank')
    p=list(range(n))
    for m in range(n,0,-1):
        j=r%m; r//=m; p[m-1],p[j]=p[j],p[m-1]
    return p
def mr_rank(p):
    p=list(p); n=len(p)
    if sorted(p)!=list(range(n)): raise ValueError('permutation')
    inv=[0]*n
    for i,v in enumerate(p): inv[v]=i
    def rec(m):
        if m<=1:return 0
        s=p[m-1]; j=inv[m-1]; p[m-1],p[j]=p[j],p[m-1]; inv[s],inv[m-1]=inv[m-1],inv[s]
        return s+m*rec(m-1)
    return rec(n)
PERMS=tuple(tuple(mr_unrank(5,r)) for r in range(64))

def _primes():
    return tuple(x for x in range(2,512) if all(x%d for d in range(2,int(x**.5)+1)))
PRIMES=_primes(); assert len(PRIMES)==97 and PRIMES[-1]==509

@dataclass(frozen=True)
class Config:
    source_bytes:int; k:int; r:int; moduli:tuple[int,...]
    @property
    def n(self):return len(self.moduli)
    @property
    def images(self):return 5*self.n
    @property
    def bound(self):return 1<<(8*self.source_bytes)
    @property
    def t(self):return self.r//2

def config(source_bytes,r=R):
    bits=8*source_bytes
    for k in range(1,len(PRIMES)-r+1):
        sel=PRIMES[-(k+r):]
        if sum(math.log2(m) for m in sel[:k])>=bits:return Config(source_bytes,k,r,sel)
    raise ValueError('source block too large')
def plan(nbytes,r=R):
    avail={}
    for n in range(1,nbytes+1):
        try:avail[n]=config(n,r)
        except ValueError:pass
    inf=10**9; dp=[(0,[])]+[(inf,None)]*nbytes
    for total in range(1,nbytes+1):
        for n,c in avail.items():
            if n<=total and dp[total-n][1] is not None:
                z=dp[total-n][0]+c.images; q=dp[total-n][1]+[c]
                if z<dp[total][0] or (z==dp[total][0] and tuple(x.source_bytes for x in q)<tuple(x.source_bytes for x in (dp[total][1] or q))): dp[total]=(z,q)
    if dp[nbytes][1] is None:raise ValueError('no plan')
    return tuple(dp[nbytes][1])

def crt(res,mods):
    x=0;M=1
    for a,m in zip(res,mods,strict=True):
        if not 0<=a<m:raise ValueError('residue')
        x+=M*(((a-x)%m)*pow(M,-1,m)%m);M*=m
    return x,M
def _conv(a,b)->Iterable[tuple[int,int]]:
    p0,p1=0,1;q0,q1=1,0
    while b:
        z=a//b;p=z*p1+p0;q=z*q1+q0;yield p,q;p0,p1=p1,p;q0,q1=q1,q;a,b=b,a-z*b
def robust(res,c:Config):
    y,M=crt(res,c.moduli); bad=lambda x:sum(x%m!=a for a,m in zip(res,c.moduli,strict=True))
    if y<c.bound and bad(y)<=c.t:return (y,)
    out=[];seen=set()
    for q,e in _conv(y,M):
        if e<=1 or M%e:continue
        x=y-q*(M//e)
        if 0<=x<c.bound and x not in seen and bad(x)<=c.t:out.append(x);seen.add(x)
    return tuple(out)

def encode_blocks(data,r=R):
    ps=plan(len(data),r); out=[]; off=0
    for c in ps:
        b=data[off:off+c.source_bytes];off+=c.source_bytes;x=int.from_bytes(b,'big')
        out.append((c,tuple(x%m for m in c.moduli)))
    return tuple(out)

def group_order(k,s,label,count):
    sk=subkey(k,b'local-permutation-group-schedule-v1'); rows=[]
    for gi in range(count):
        m=b'group-order:'+s.to_bytes(8,'big')+label.to_bytes(1,'big')+gi.to_bytes(2,'big')
        rows.append((hmac.new(sk,m,hashlib.sha256).digest(),gi))
    return tuple(gi for _,gi in sorted(rows))

def mapping(k,s): return keyed_permutation(8,subkey(k,b'cluster-mapping'),s)

def encode_groups(payload,sequence,key,identifiers,banks,r=R):
    protected=protect(payload,key,sequence); blocks=encode_blocks(protected,r); total=sum(len(v) for _,v in blocks)
    if total>min(len(banks.get(i,())) for i in range(8)):raise ValueError('group bank capacity')
    mp=mapping(key,sequence); schedules={i:group_order(key,sequence,i,len(banks[i])) for i in range(8)}
    groups=[];used=set();j=0
    for _,res in blocks:
        for v in res:
            sym,rank=v>>6,v&63; label=mp[sym]; g=sorted(banks[label][schedules[label][j]]); tx=tuple(g[t] for t in PERMS[rank])
            if used.intersection(tx):raise RuntimeError('cover reuse')
            used.update(tx);groups.append(tuple(identifiers[t] for t in tx));j+=1
    return protected,tuple(c for c,_ in blocks),tuple(groups)

def normalize(x):
    x=np.asarray(x,float);return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)
def templates(clean,cal,attack_order):
    cn=normalize(clean); general=np.stack([cn]+[normalize(cal[a]) for a in attack_order],axis=1)
    c5=normalize(cal['crop_05']);c10=normalize(cal['crop_10']);mid=normalize(c5+c10);ext=normalize(2*c10-c5)
    return {'crop':np.stack([cn,c5,mid,c10,ext],axis=1),'general':general}

def residue_candidates(received,modulus,j,sequence,key,banks,refs,limit=CANDIDATES):
    mp=mapping(key,sequence); schedules={i:group_order(key,sequence,i,len(banks[i])) for i in range(8)}; arr=[]; received=np.asarray(received,float)
    for sym in range(8):
        base=sym<<6
        if base>=modulus:break
        label=mp[sym]; expected=np.asarray(sorted(banks[label][schedules[label][j]]),int)
        sim=np.max(np.einsum('id,jtd->ijt',received,refs[expected]),axis=2); scores=sim[np.arange(5)[None,:],np.asarray(PERMS)].sum(1)
        arr.extend((base+r,float(scores[r])) for r in range(min(64,modulus-base)))
    arr.sort(key=lambda z:(-z[1],z[0]));return tuple(arr[:limit])

def _protected_candidates(vector,configs):
    off=0; blocks=[]
    for c in configs:
        vals=robust(vector[off:off+c.n],c);off+=c.n
        if not vals:return ()
        blocks.append(tuple(x.to_bytes(c.source_bytes,'big') for x in vals))
    return tuple(b''.join(q) for q in product(*blocks))
def decode_lists(lists,configs,key,sequence,width=BEAM_WIDTH,positions_n=BEAM_POSITIONS):
    if any(not x for x in lists):raise ValueError('empty candidate list')
    top=[x[0][0] for x in lists]
    def check(v):
        for c in _protected_candidates(v,configs):
            try:return unprotect(c,key,sequence)
            except (InvalidTag,ValueError):pass
        return None
    p=check(top)
    if p is not None:return p,{'mode':'hard','tested':1,'depth':0}
    pos=[i for _,i in sorted((x[0][1]-x[1][1],i) for i,x in enumerate(lists) if len(x)>1)[:positions_n]]; beam=[(0.,())];tested=1
    for depth,i in enumerate(pos,1):
        nxt=[];base=lists[i][0][1]
        for cost,ch in beam:
            nxt.append((cost,ch))
            for rank in range(1,len(lists[i])):nxt.append((cost+max(0.,base-lists[i][rank][1]),ch+((i,rank),)))
        nxt.sort(key=lambda z:(z[0],len(z[1]),z[1]));beam=nxt[:width]
        for _,ch in beam:
            if not ch:continue
            v=top.copy()
            for q,rank in ch:v[q]=lists[q][rank][0]
            tested+=1;p=check(v)
            if p is not None:return p,{'mode':'beam','tested':tested,'depth':depth}
    raise ValueError(f'decode failed after {tested} states')

def decode_embeddings(groups,payload_bytes,sequence,key,banks,hypotheses,r=R):
    configs=plan(payload_bytes+16,r); mods=tuple(m for c in configs for m in c.moduli)
    if len(groups)!=len(mods):raise ValueError('group count')
    errors=[]
    for h,refs in enumerate(hypotheses):
        lists=tuple(residue_candidates(g,m,j,sequence,key,banks,refs) for j,(g,m) in enumerate(zip(groups,mods,strict=True)))
        try:
            p,d=decode_lists(lists,configs,key,sequence)
            if len(p)!=payload_bytes:raise ValueError('payload length')
            return p,{**d,'template_hypothesis':h}
        except ValueError as e:errors.append(str(e))
    raise ValueError('all template hypotheses failed: '+' | '.join(errors))
