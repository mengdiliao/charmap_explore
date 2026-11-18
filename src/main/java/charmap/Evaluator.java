package charmap;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Identical legacy statistic definitions, common construction and weighted evaluation. */
final class Evaluator {
    final Core.Data d;final int P,B,np,nw,last;final Path out;final String mode;
    final LinkedHashMap<String,Component> comps=new LinkedHashMap<>();
    final ArrayList<Method> methods=new ArrayList<>();
    static final class Component{
        final String name,kind;final int bytes,p,q,k,nw;final int[] positions;final long[] post;
        long ndv,occupied;final long[] exact=new long[2];
        Component(String n,String kind,int b,int p,int q,int k,int nw,int[] positions){
            this.name=n;this.kind=kind;bytes=b;this.p=p;this.q=q;this.k=k;this.nw=nw;this.positions=positions;post=new long[Math.multiplyExact(b*8,nw)];
        }
        int bit(String s,long h,int j){
            return switch(kind){
                case "pos" -> Core.ch(s,p)%128;
                case "len" -> Math.min(s.length(),bytes*8-1);
                case "pair" -> Core.bucket(Core.mix(Core.pair(s,p,q)),bytes*8);
                case "tuple4","joint" -> Core.bucket(Core.mix(Core.token(s,positions)),bytes*8);
                default -> Core.bucket(Core.mix(h+j*0x9e3779b97f4a7c15L),bytes*8);
            };
        }
        void add(String s,long h,int pid){for(int j=0;j<k;j++){int b=bit(s,h,j);post[b*nw+pid/64]|=1L<<(pid%64);}}
        String schema(){String s=name+":"+kind+":"+bytes+":"+p+":"+q+":"+k;if(kind.equals("joint"))for(int x:positions)s+=":"+x;return s;}
    }
    static final class Method{
        final String name;final Component[] cs;long bytes,meta;final long[] ret=new long[2],fn=new long[2],neg=new long[2],rows=new long[2];
        Method(String n,Component... cs){name=n;this.cs=cs;}
        String desc(){return String.join(";",Arrays.stream(cs).map(c->c.name).toList());}
    }
    Evaluator(Core.Data d,int P,int B,Path out,String mode){
        this.d=d;this.P=P;this.B=B;this.out=out;this.mode=mode;
        if(P<1||B<32||B%8!=0)throw new IllegalArgumentException("Invalid P/B");
        np=(d.keys.size()+P-1)/P;nw=(np+63)/64;last=d.keys.size()-(np-1)*P;d.partition(P);
    }
    Component add(String n,String kind,int b,int p,int q,int k,int[] positions){
        return comps.computeIfAbsent(n,x->new Component(n,kind,b,p,q,k,nw,positions));
    }
    Component pos(int p){return add("pos"+p,"pos",16,p,0,1,null);}
    Component bloom(int b){int k=Core.optimalK(P,b);return add("bloom"+b+"_k"+k,"bloom",b,0,0,k,null);}
    Component len(){return add("length64","len",8,0,0,1,null);}
    Component pair(){return add("pair_first_last128","pair",16,0,-1,1,null);}
    Component tuple(int b){return add("tuple4_"+b,"tuple4",b,0,0,1,Core.REF);}
    void method(String n,Component... c){methods.add(new Method(n,c));}
    void setup(Path candidates)throws IOException{
        method("OptimizedBloom",bloom(B));
        if(mode.equals("position")){
            HashSet<String> names=new HashSet<>(List.of("OptimizedBloom","Oracle"));
            for(String line:Files.readAllLines(candidates)){
                String[] fields=line.strip().split("\\s+");int[] pp=Arrays.stream(fields).skip(1).mapToInt(Integer::parseInt).toArray();
                if(!fields[0].matches("[A-Za-z0-9_]+")||!names.add(fields[0])||pp.length<2||pp.length>6||Arrays.stream(pp).distinct().count()!=pp.length||Arrays.stream(pp).anyMatch(x->x< -16||x>15))throw new IOException("Invalid candidate: "+line);
                method(fields[0],add(fields[0],"joint",B,0,0,1,pp));
            }
            return;
        }
        boolean pilot=mode.equals("pilot");
        ArrayList<Component> a=new ArrayList<>(),e=new ArrayList<>();
        int n=pilot?B/16:Math.min(B/16,Math.min(64,d.maxlen));
        int z=pilot?B/32:Math.min(B/32,Math.min(32,d.maxlen));
        for(int i=0;i<n;i++)a.add(pos(i));
        for(int i=0;i<z;i++){e.add(pos(i));e.add(pos(-1-i));}
        method("FixedCharacterMap",a.toArray(Component[]::new));method("PrefixSuffixCharacterMap",e.toArray(Component[]::new));
        if(!pilot)method("JointCharacterMap",tuple(B));
        method("PrefixCM+Bloom",pos(0),bloom(B-16));method("SuffixCM+Bloom",pos(-1),bloom(B-16));
        if(pilot&&B>=64)method("PrefixSuffixCM+Bloom",pos(0),pos(-1),bloom(B-32));
        method("JointCM+Bloom",pair(),bloom(B-16));method("Length+Bloom",len(),bloom(B-8));
        if(pilot&&B>=64)method("Length+SuffixCM+Bloom",len(),pos(-1),bloom(B-24));
        if(!pilot){int b=Math.max(16,B/8);method("ScaledJointCM+Bloom",tuple(b),bloom(B-b));}
    }
    static String prefix(String s){return (s+"\0".repeat(16)).substring(0,16);}
    static int lower(String[] a,String s,boolean upper){int l=0,r=a.length;while(l<r){int m=(l+r)>>>1;int c=a[m].compareTo(s);if(c<0||(upper&&c==0))l=m+1;else r=m;}return l;}
    void serialize(Method m)throws IOException{
        String schema=m.name;int b=0;for(Component c:m.cs){schema+=";"+c.schema();b+=c.bytes;}
        if(b>B||b==0)throw new IOException("budget");m.bytes=b;Path path=out.resolve(m.name+".bin");
        try(var f=new BufferedOutputStream(Files.newOutputStream(path))){
            Core.header(f,np,b,schema);
            for(int pid=0;pid<np;pid++)for(Component c:m.cs)for(int j=0;j<c.bytes;j++){
                int v=0;for(int bit=0;bit<8;bit++)if((c.post[(j*8+bit)*nw+pid/64]&(1L<<(pid%64)))!=0)v|=1<<bit;f.write(v);}
        }
        m.meta=Files.size(path);if(m.meta!=16+schema.length()+(long)np*b)throw new IOException("serialized size");
    }
    void diagnostics(Component c){
        if(!c.kind.equals("joint"))return;
        HashMap<Long,long[]> q=new HashMap<>();
        for(var e:d.records.entrySet()){var f=e.getValue().freq;if(f[0]==0&&f[1]==0)continue;long t=Core.token(e.getKey(),c.positions);long[] a=q.computeIfAbsent(t,x->new long[2]);a[0]+=f[0];a[1]+=f[1];}
        long[] tokens=new long[P];
        for(int i=0;i<d.keys.size();i+=P){int n=Math.min(P,d.keys.size()-i);for(int j=0;j<n;j++)tokens[j]=Core.token(d.keys.get(i+j),c.positions);Arrays.sort(tokens,0,n);
            for(int j=0;j<n;j++)if(j==0||tokens[j]!=tokens[j-1]){c.ndv++;long[] f=q.get(tokens[j]);if(f!=null){c.exact[0]+=f[0];c.exact[1]+=f[1];}}}
        for(long x:c.post)c.occupied+=Long.bitCount(x);
    }
    void run(Path candidates)throws IOException{
        Files.createDirectories(out);setup(candidates);
        boolean mm=mode.equals("sensitivity")||(mode.equals("pilot")&&B==32);
        String[] mins=new String[np],maxs=new String[np];long mmmeta=0;
        // Build each unique component once.
        Component[] all=comps.values().toArray(Component[]::new);
        for(int i=0;i<d.keys.size();i++){String s=d.keys.get(i);int pid=i/P;long h=Core.hash(s);for(Component c:all)c.add(s,h,pid);
            if(mm){String x=prefix(s);if(i%P==0)mins[pid]=maxs[pid]=x;else{if(x.compareTo(mins[pid])<0)mins[pid]=x;if(x.compareTo(maxs[pid])>0)maxs[pid]=x;}}}
        for(Component c:all)diagnostics(c);
        for(Method m:methods)serialize(m);
        if(mm){Path path=out.resolve("MinMax32.bin");try(var f=new BufferedOutputStream(Files.newOutputStream(path))){Core.header(f,np,32,"MinMax32:fixed zero-padded 16-byte prefix bounds");for(int i=0;i<np;i++){f.write(mins[i].getBytes(StandardCharsets.US_ASCII));f.write(maxs[i].getBytes(StandardCharsets.US_ASCII));}}mmmeta=Files.size(path);}
        String[] lo=mins.clone(),hi=maxs.clone();if(mm){Arrays.sort(lo);Arrays.sort(hi);}
        long[] orows=new long[2],mr=new long[2],mf=new long[2],mn=new long[2],mrows=new long[2];
        // Preallocate per-query component bit offsets; preserve original frequencies.
        IdentityHashMap<Component,Integer> ci=new IdentityHashMap<>();for(int i=0;i<all.length;i++)ci.put(all[i],i);
        int[][] offset=new int[all.length][];for(int i=0;i<all.length;i++)offset[i]=new int[all[i].k];
        int[][] mi=new int[methods.size()][];for(int i=0;i<mi.length;i++)mi[i]=Arrays.stream(methods.get(i).cs).mapToInt(ci::get).toArray();
        long[] temp=new long[nw];
        for(var entry:d.records.entrySet()){
            String s=entry.getKey();Core.Record rec=entry.getValue();long[] f=rec.freq;if(f[0]==0&&f[1]==0)continue;int pid=rec.pid;boolean member=pid>=0;
            if(member)for(int w=0;w<2;w++)orows[w]+=f[w]*(pid==np-1?last:P);
            if(mm){String x=prefix(s);int n=lower(lo,x,true)-lower(hi,x,false);boolean lp=x.compareTo(mins[np-1])>=0&&x.compareTo(maxs[np-1])<=0;
                boolean bad=member&&(x.compareTo(mins[pid])<0||x.compareTo(maxs[pid])>0);
                for(int w=0;w<2;w++){mr[w]+=f[w]*n;mrows[w]+=f[w]*((long)n*P-(lp?P-last:0));if(bad)mf[w]+=f[w];if(!member)mn[w]+=f[w]*n;}}
            long h=Core.hash(s);for(int i=0;i<all.length;i++)for(int j=0;j<all[i].k;j++)offset[i][j]=all[i].bit(s,h,j)*nw;
            for(int i=0;i<methods.size();i++){Method method=methods.get(i);int[] indexes=mi[i];long count=0;
                for(int w=0;w<nw;w++){long v=-1L;outer:for(int id:indexes)for(int off:offset[id]){v&=all[id].post[off+w];if(v==0)break outer;}temp[w]=v;count+=Long.bitCount(v);}
                boolean bad=member&&(temp[pid/64]&(1L<<(pid%64)))==0;
                boolean lp=(temp[(np-1)/64]&(1L<<((np-1)%64)))!=0;
                for(int w=0;w<2;w++){method.ret[w]+=f[w]*count;method.rows[w]+=f[w]*(count*P-(lp?P-last:0));if(bad)method.fn[w]+=f[w];if(!member)method.neg[w]+=f[w]*count;}
            }
        }
        try(var csv=Core.writer(out.resolve("results.csv"))){
            String header="workload,algorithm,budget_bytes,partition_size,partitions,dataset_rows,unique_stored,nonascii_rows,queries,global_positive,global_negative,query_partition_pairs,oracle_retained,retained,false_positive_pairs,false_negatives,pruning_pct,negative_pruning_pct,metadata_total_bytes,bpk";
            if(mode.equals("pilot"))header+=",components";else header+=",payload_used_bytes,nominal_bpk,partition_fpr_pct,oracle_capture_pct,retained_rows_pct,components";
            if(mode.equals("position"))header+=",positions,mean_token_ndv,mean_saturation_pct,collision_excess_pct,exact_joint_pruning_pct,bloom_k";
            csv.println(header);System.out.println(header);
            for(int w=0;w<2;w++){
                emit(csv,w,"Oracle",d.positive[w],0,0,0,0,orows[w],"exact",null);
                if(mm)emit(csv,w,"MinMax32",mr[w],mf[w],mn[w],mmmeta,32,mrows[w],"prefix16 bounds",null);
                for(Method m:methods)emit(csv,w,m.name,m.ret[w],m.fn[w],m.neg[w],m.meta,m.bytes,m.rows[w],m.desc(),m);
            }
        }
    }
    void emit(PrintWriter csv,int w,String name,long ret,long fn,long negret,long meta,long used,long rows,String desc,Method m){
        long q=d.queries[w],oracle=d.positive[w],pairs=q*np,neg=q-oracle;int n=d.keys.size();
        if(fn!=0||ret<oracle)throw new IllegalStateException("False negative "+name);
        String s=Core.csv(Core.WORK[w],name,mode.equals("pilot")&&name.equals("Oracle")?0:B,P,np,n,n,0,q,oracle,neg,pairs,oracle,ret,ret-oracle,fn,Core.pct(pairs-ret,pairs),Core.pct(neg*np-negret,neg*np),meta,8.0*meta/n);
        if(!mode.equals("pilot"))s+=","+Core.csv(used,8.0*B/P,Core.pct(ret-oracle,pairs-oracle),Core.pct(pairs-ret,pairs-oracle),Core.pct(rows,q*n));
        s+=","+desc;
        if(mode.equals("position")){
            if(m==null)s+=",,,,,,";
            else {Component c=m.cs[0];if(c.kind.equals("joint")){if(ret<c.exact[w])throw new IllegalStateException("Above exact ceiling");s+=","+Core.csv(Core.positions(c.positions),(double)c.ndv/np,Core.pct(c.occupied,(long)c.bytes*8*np),Core.pct(c.ndv-c.occupied,c.ndv),Core.pct(pairs-c.exact[w],pairs),"");}
            else s+=",,,,,,"+c.k;}
        }
        csv.println(s);System.out.println(s);
    }
}
