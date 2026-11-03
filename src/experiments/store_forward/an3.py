import json,collections,statistics as st
G=collections.defaultdict(dict)
import os,sys
d=sys.argv[1] if len(sys.argv)>1 else 'output/store_forward_20261103'
for f in[os.path.join(d,x) for x in('results.jsonl','results_rr.jsonl','results_sf.jsonl')]:
    for l in open(f):
        r=json.loads(l)
        G[(r['topo'],r['N'],r['M'],r['seed'])][r['m']]=r
T=collections.defaultdict(lambda:dict(n=0,s=0,sr=0,c=0,ds=0,dr=0,e=0,l=0,bad=0,stop=0,sec=0,mx=0,seeds=0,full=0,tot=0,diff=[]))
for k,d in sorted(G.items(),key=str):
    if 'sf' not in d or 'sr10' not in d: continue
    n=min(len(d['sf']['rows']),len(d['sr10']['rows']))
    t=T[k[:3]];t['seeds']+=1;t['n']+=n;t['tot']+=k[1];t['bad']+=d['sf']['bad'];t['stop']+=1 if d['sf']['stop'] else 0
    ds=dr=0
    for x,y in zip(d['sf']['rows'][:n],d['sr10']['rows'][:n]):
        a,b=x['arr'] is not None,y['arr'] is not None
        ds+=a;dr+=b;t['sec']+=x['sec'];t['mx']=max(t['mx'],x['sec'])
        if a and b:
            p,q=x['arr']-x['g'],y['arr']-y['g'];t['c']+=1;t['ds']+=p;t['dr']+=q;t['e']+=p<q-1e-9;t['l']+=p>q+1e-9
    t['s']+=ds;t['sr']+=dr;t['diff'].append(ds-dr)
for k,t in sorted(T.items(),key=str):
    dd=t['diff'];ci=(2.093*st.stdev(dd)/len(dd)**.5) if len(dd)==20 else None
    print(k,f"seeds={t['seeds']} n={t['n']}/{t['tot']} sf={t['s']}({t['s']/t['n']:.1%}) sr10={t['sr']}({t['sr']/t['n']:.1%}) bad={t['bad']} stop={t['stop']} sec/b={t['sec']/t['n']:.3f} max={t['mx']:.1f} common={t['c']} d={t['ds']/max(t['c'],1):.1f}/{t['dr']/max(t['c'],1):.1f} ({(t['ds']-t['dr'])/max(t['dr'],1):+.2%}) e/l={t['e']}/{t['l']} W/T/L={sum(x>0 for x in dd)}/{sum(x==0 for x in dd)}/{sum(x<0 for x in dd)} mean={st.mean(dd):.2f}"+(f"±{ci:.2f}" if ci else ""))
