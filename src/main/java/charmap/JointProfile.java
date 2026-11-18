package charmap;

import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Same full-workload joint projection diagnostic and CSV schema as legacy C++. */
public final class JointProfile {
    static final String[] SOURCES={"dataset","uniform","zipf"};
    static long token(String s,boolean four){return four?Core.token(s,Core.REF):Core.pair(s,0,-1);}
    static String printable(long t,boolean four){
        int base=four?257:256;int[] a=new int[four?4:2];
        for(int i=a.length-1;i>=0;i--){a[i]=(int)(t%base);t/=base;}
        StringBuilder b=new StringBuilder();
        for(int c:a){if(c==128)b.append("<MISSING>");else if(c>=32&&c<127&&c!=','&&c!='\\'&&c!='"')b.append((char)c);else b.append(String.format(Locale.ROOT,"\\x%02x",c));}
        return b.toString();
    }
    static int quantile(int[] a,double p){int[] b=a.clone();Arrays.sort(b);return b[(int)Math.ceil(p*b.length)-1];}
    static final class Config {
        final int bytes,m;final long[] uniform,zipf;final BitSet global;
        long occ,loss,ur,zr;final int[] occupied;
        Config(int b,int np,Map<Long,long[]> table){
            bytes=b;m=b*8;uniform=new long[m];zipf=new long[m];global=new BitSet(m);occupied=new int[np];
            for(var e:table.entrySet()){int i=Core.bucket(Core.mix(e.getKey()),m);long[] f=e.getValue();if(f[0]>0)global.set(i);uniform[i]+=f[1];zipf[i]+=f[2];}
        }
        void add(long[] hash,int n,int pid){
            BitSet b=new BitSet(m);int k=0;
            for(int j=0;j<n;j++){int i=Core.bucket(hash[j],m);if(b.get(i))continue;b.set(i);k++;ur+=uniform[i];zr+=zipf[i];}
            occ+=k;loss+=n-k;occupied[pid]=k;
        }
    }
    public static void main(String[] args)throws Exception{
        if(args.length!=2)throw new IllegalArgumentException("data_dir output_dir");
        Core.Data d=new Core.Data(Path.of(args[0]),55);Path out=Path.of(args[1]);Files.createDirectories(out);
        if(d.keys.size()!=2926705||d.queries[0]!=10000000||d.queries[1]!=10000000)throw new IOException("wrong input counts");
        try(var g=Core.writer(out.resolve("global.csv"));var t=Core.writer(out.resolve("top_tokens.csv"));var p=Core.writer(out.resolve("partitions.csv"));var b=Core.writer(out.resolve("bitmaps.csv"))){
            g.println("tuple,source,rows,ndv,missing_rows,unseen_dataset_ndv,unseen_dataset_rows,top1_pct,top10_pct");
            t.println("tuple,source,rank,token,frequency,share_pct,dataset_frequency,uniform_frequency,zipf_frequency");
            p.println("tuple,partition_size,partitions,ndv_min,ndv_mean,ndv_median,ndv_p95,ndv_max,uniform_exact_pruning_pct,zipf_exact_pruning_pct");
            b.println("tuple,partition_size,partitions,budget_bytes,nominal_bpk,global_dataset_ndv,global_occupied_bits,global_collision_excess_pct,mean_occupied_bits,median_occupied_bits,p95_occupied_bits,mean_saturation_pct,partition_collision_excess_pct,uniform_hash_pruning_pct,zipf_hash_pruning_pct,uniform_collision_loss_pp,zipf_collision_loss_pp");
            d.partition(d.keys.size());
            for(boolean four:new boolean[]{false,true}){
                String label=four?"four":"pair";HashMap<Long,long[]> table=new HashMap<>();long[] missing=new long[3],tot={d.keys.size(),d.queries[0],d.queries[1]};
                for(var e:d.records.entrySet()){
                    String s=e.getKey();Core.Record rec=e.getValue();long[] f=table.computeIfAbsent(token(s,four),x->new long[3]);
                    long[] a={rec.pid>=0?1:0,rec.freq[0],rec.freq[1]};
                    for(int j=0;j<3;j++){f[j]+=a[j];if(s.length()<(four?2:1))missing[j]+=a[j];}
                }
                long globalndv=table.values().stream().filter(a->a[0]>0).count();
                for(int src=0;src<3;src++){
                    final int j=src;var freq=table.entrySet().stream().filter(e->e.getValue()[j]>0).sorted(Comparator.<Map.Entry<Long,long[]>>comparingLong(e->e.getValue()[j]).reversed().thenComparingLong(Map.Entry::getKey)).toList();
                    long unseen=0,unseenrows=0,top=0;for(var e:freq)if(e.getValue()[0]==0){unseen++;unseenrows+=e.getValue()[j];}
                    for(int i=0;i<Math.min(10,freq.size());i++){var e=freq.get(i);long[] a=e.getValue();top+=a[j];Core.row(t,label,SOURCES[j],i+1,printable(e.getKey(),four),a[j],Core.pct(a[j],tot[j]),a[0],a[1],a[2]);}
                    Core.row(g,label,SOURCES[j],tot[j],freq.size(),missing[j],unseen,unseenrows,Core.pct(freq.get(0).getValue()[j],tot[j]),Core.pct(top,tot[j]));
                }
                long[] tokens=new long[d.keys.size()];for(int i=0;i<tokens.length;i++)tokens[i]=token(d.keys.get(i),four);
                for(int P:new int[]{500,2000,8000,32000,128000}){
                    int np=(tokens.length+P-1)/P;
                    TreeSet<Integer> budgets=new TreeSet<>(List.of(16,32,64,128,256));for(int x:new int[]{32,64,128,256}){budgets.add(x*P/500);budgets.add(Math.max(16,x*P/500/8));}
                    ArrayList<Config> cs=new ArrayList<>();for(int size:budgets)cs.add(new Config(size,np,table));
                    int[] ndvs=new int[np];long ndvsum=0,eu=0,ez=0;long[] block=new long[P],hashed=new long[P];
                    for(int pid=0;pid<np;pid++){
                        int start=pid*P,n=Math.min(P,tokens.length-start);System.arraycopy(tokens,start,block,0,n);Arrays.sort(block,0,n);
                        int k=0;for(int i=0;i<n;i++)if(i==0||block[i]!=block[i-1]){long id=block[i];long[] f=table.get(id);eu+=f[1];ez+=f[2];hashed[k++]=Core.mix(id);}
                        ndvs[pid]=k;ndvsum+=k;for(Config c:cs)c.add(hashed,k,pid);
                    }
                    long up=tot[1]*np,zp=tot[2]*np;double ex1=100.0*(1-(double)eu/up),ex2=100.0*(1-(double)ez/zp);
                    Core.row(p,label,P,np,Arrays.stream(ndvs).min().orElseThrow(),(double)ndvsum/np,quantile(ndvs,.5),quantile(ndvs,.95),Arrays.stream(ndvs).max().orElseThrow(),ex1,ex2);
                    for(Config c:cs){double pr1=100.0*(1-(double)c.ur/up),pr2=100.0*(1-(double)c.zr/zp);if(pr1>ex1+1e-8||pr2>ex2+1e-8)throw new IllegalStateException("inconsistent hash pruning");
                        Core.row(b,label,P,np,c.bytes,8.0*c.bytes/P,globalndv,c.global.cardinality(),Core.pct(globalndv-c.global.cardinality(),globalndv),(double)c.occ/np,quantile(c.occupied,.5),quantile(c.occupied,.95),Core.pct(c.occ,(long)np*c.m),Core.pct(c.loss,ndvsum),pr1,pr2,ex1-pr1,ex2-pr2);}
                    System.err.println(label+" P="+P+" complete");
                }
            }
        }
    }
}
