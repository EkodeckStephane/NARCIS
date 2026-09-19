import os
import pytest
from cryptography.exceptions import InvalidTag
from narcis.perm_rrns_core import PRIMES,PERMS,config,plan,mr_rank,mr_unrank,protect,unprotect,nonce,robust,encode_blocks,encode_groups,decode_lists

def banks():
    ids=[];b={};p=0
    for label in range(8):
        gs=[]
        for gi in range(175):
            g=[]
            for mi in range(5):ids.append(f'{label}/{gi}/{mi}');g.append(p);p+=1
            gs.append(tuple(g))
        b[label]=tuple(gs)
    return ids,b

def test_rank_all_s5():
    for r in range(120):assert mr_rank(mr_unrank(5,r))==r
    assert len(set(PERMS))==64

def test_compact_aead():
    k=os.urandom(32);p=b'12345678';c=protect(p,k,7);assert len(c)==24 and unprotect(c,k,7)==p and nonce(k,7)!=nonce(k,8)
    with pytest.raises(InvalidTag):unprotect(c,k,8)

def test_frozen_traffic_points():
    c=config(24,18);assert (c.k,c.r,c.n,c.images,c.moduli[0],c.moduli[-1])==(23,18,41,205,269,509)
    assert sum(x.images for x in plan(48,18))==335
    assert sum(x.images for x in plan(80,18))==580

def test_rrns_nine_errors():
    data=bytes(range(24));c=config(24,18);x=int.from_bytes(data,'big');res=[x%m for m in c.moduli]
    for i in range(9):res[i]=(res[i]+1)%c.moduli[i]
    assert x in robust(res,c)

def test_encode_8b_uses_205_distinct_images():
    ids,b=banks();protected,configs,groups=encode_groups(b'ABCDEFGH',3,b'K'*32,ids,b)
    assert len(protected)==24 and len(groups)==41 and sum(map(len,groups))==205 and len(set(x for g in groups for x in g))==205

def test_aead_accepts_rrns_corrected_candidate_vector():
    k=b'Z'*32;p=b'12345678';prot=protect(p,k,11);blocks=encode_blocks(prot,18);configs=tuple(c for c,_ in blocks);lists=[]
    mods=[]
    for c,res in blocks:
        for m,v in zip(c.moduli,res):mods.append(m);lists.append([(v,0.)])
    for i in range(9):lists[i]=[((lists[i][0][0]+1)%mods[i],0.)]
    out,d=decode_lists(lists,configs,k,11);assert out==p and d['mode']=='hard'
