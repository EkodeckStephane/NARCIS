from argparse import ArgumentParser
from pathlib import Path
import base64, hashlib, importlib.util, json, sys, zlib
import numpy as np, pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"src"),str(ROOT/"tools")]
from narcis.glcm import glcm_texture_features
from run_bossbase_campaign import residual_features
from tomm_final_detector_audit import forest_probabilities,safe_auc

PAYLOAD_SHA="ac7fefd1e216e11216ac3575beb7de37874523d9efbd00972c9c6186088b7431"

def payload_module():
    parts=sorted((ROOT/"tools"/".tomm_frozen_payload").glob("part*.b64"))
    raw=zlib.decompress(base64.b64decode("".join(p.read_text().strip() for p in parts)))
    assert hashlib.sha256(raw).hexdigest()==PAYLOAD_SHA
    p=ROOT/"tools"/".tomm_frozen_payload_runtime.py"; p.write_bytes(raw)
    spec=importlib.util.spec_from_file_location("frozen",p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m,p

def features(dataset,out):
    srmp=out/"srm52_features.npy"; glp=out/"glcm5_features.npy"
    if srmp.exists() and glp.exists(): return np.load(srmp),np.load(glp)
    srm=[]; gl=[]
    for i in range(len(dataset)):
        x,_=dataset[i]; a=x.numpy(); srm.append(residual_features(a)); gl.append(glcm_texture_features(a))
        if (i+1)%500==0: print("features",i+1,flush=True)
    srm=np.asarray(srm,np.float32); gl=np.asarray(gl,np.float64); np.save(srmp,srm); np.save(glp,gl); return srm,gl

def run(dataset,target,seed,out,repeats):
    srm,gl=features(dataset,out); idx=np.arange(len(dataset)); rows=[]
    for r in range(repeats):
        ss=seed*10000+r; tr,te=train_test_split(idx,test_size=.35,random_state=ss,shuffle=True)
        f=ExtraTreesClassifier(n_estimators=300,max_features="sqrt",class_weight="balanced",random_state=ss,n_jobs=-1)
        f.fit(srm[tr],target[tr]); pp=forest_probabilities(f,srm[te])
        sa=[safe_auc(target[te,h],pp[h]) for h in range(target.shape[1])]
        ga=[]
        for h in range(target.shape[1]):
            y=target[:,h]; c=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",random_state=ss))
            c.fit(gl[tr],y[tr]); ga.append(safe_auc(y[te],c.predict_proba(gl[te])[:,1]))
        row={"dataset":"Caltech-101","partition_seed":seed,"repeat":r,"split_seed":ss,
             "srm52_extratrees_macro_auc":float(np.nanmean(sa)),"glcm5_logistic_macro_auc":float(np.nanmean(ga))}
        rows.append(row); pd.DataFrame(rows).to_csv(out/"classical_repetitions.csv",index=False); print(json.dumps(row),flush=True)
    return pd.DataFrame(rows)

def main():
    a=ArgumentParser(); a.add_argument("--dataset-root",type=Path,required=True); a.add_argument("--output",type=Path,required=True)
    a.add_argument("--seed",type=int,required=True); a.add_argument("--repeats",type=int,default=20); x=a.parse_args(); x.output.mkdir(parents=True,exist_ok=True)
    m,p=payload_module()
    def patched(*,dataset,target,seed,output,repeats): return run(dataset,target,seed,output,repeats),pd.DataFrame()
    m.run_detectors=patched
    m.summarize=lambda d: {"srm52_extratrees_macro_auc":{"mean":float(d.srm52_extratrees_macro_auc.mean())},
                           "glcm5_logistic_macro_auc":{"mean":float(d.glcm5_logistic_macro_auc.mean())}}
    old=sys.argv[:]
    try: sys.argv=[str(p),"--dataset-root",str(x.dataset_root),"--output",str(x.output),"--seed",str(x.seed),"--repeats",str(x.repeats)]; m.main()
    finally: sys.argv=old; p.unlink(missing_ok=True)
if __name__=="__main__": main()
