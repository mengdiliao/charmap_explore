package charmap;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Shared ASCII input, unsigned hashes, and reproducible libstdc++ layout. */
final class Core {
    static final int[] REF={0,1,-2,-1};
    static final String[] WORK={"uniform","zipf"};
    static long mix(long x) {
        x=(x^(x>>>30))*0xbf58476d1ce4e5b9L;
        x=(x^(x>>>27))*0x94d049bb133111ebL;
        return x^(x>>>31);
    }
    static long hash(String s) {
        long h=0xcbf29ce484222325L;
        for(int i=0;i<s.length();i++) {h^=s.charAt(i);h*=1099511628211L;}
        return mix(h);
    }
    static int ch(String s,int p) {
        int i=p>=0?p:s.length()+p;
        return i<0||i>=s.length()?128:s.charAt(i);
    }
    static long token(String s,int[] pos) {
        long v=0;for(int p:pos)v=v*257+ch(s,p);return v;
    }
    static long pair(String s,int p,int q){return ch(s,p)*256L+ch(s,q);}
    static int bucket(long x,int m){return (int)Long.remainderUnsigned(x,m);}
    static int optimalK(int P,int B){
        int k=1;double best=1;
        for(int i=1;i<=16;i++){double f=Math.pow(1-Math.exp(-(double)i*P/(B*8)),i);if(f<best){k=i;best=f;}}
        return k;
    }
    static final class MT64 {
        final long[] s=new long[312];int index=312;
        MT64(long seed){s[0]=seed;for(int i=1;i<312;i++)s[i]=6364136223846793005L*(s[i-1]^(s[i-1]>>>62))+i;}
        long next(){
            if(index==312){
                for(int i=0;i<312;i++){long x=(s[i]&0xffffffff80000000L)|(s[(i+1)%312]&0x7fffffffL);
                    s[i]=s[(i+156)%312]^(x>>>1)^((x&1)!=0?0xb5026f5aa96619e9L:0);}
                index=0;
            }
            long x=s[index++];x^=(x>>>29)&0x5555555555555555L;x^=(x<<17)&0x71d67fffeda60000L;x^=(x<<37)&0xfff7eee000000000L;return x^(x>>>43);
        }
        // libstdc++ 64-bit uniform_int_distribution: unbiased Lemire downscaling.
        long below(long bound){
            long x=next(),lo=x*bound;
            if(Long.compareUnsigned(lo,bound)<0){
                long threshold=Long.remainderUnsigned(-bound,bound);
                while(Long.compareUnsigned(lo,threshold)<0){x=next();lo=x*bound;}
            }
            return Math.unsignedMultiplyHigh(x,bound);
        }
    }
    // GCC/libstdc++ std::shuffle fast path, pinned explicitly for cross-platform parity.
    static void shuffle(List<String> a,long seed){
        MT64 rng=new MT64(seed);int n=a.size(),i=1;
        if(n<2)return;
        if(n%2==0){Collections.swap(a,1,(int)rng.below(2));i++;}
        while(i<n){long b=i+1L;long x=rng.below(b*(b+1));Collections.swap(a,i,(int)(x/(b+1)));i++;
            Collections.swap(a,i,(int)(x%(b+1)));i++;}
    }
    static final class Record {
        int pid=-1;final long[] freq=new long[2];
    }
    static final class Data {
        final ArrayList<String> keys=new ArrayList<>();
        final HashMap<String,Record> records=new HashMap<>(4_000_000);
        final long[] queries=new long[2],positive=new long[2];int maxlen;
        Data(Path dir,long seed)throws IOException{
            try(var r=Files.newBufferedReader(dir.resolve("dataset.txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){if(records.putIfAbsent(s,new Record())!=null)throw new IOException("Duplicate stored key");keys.add(s);maxlen=Math.max(maxlen,s.length());}
            }
            if(keys.isEmpty())throw new IOException("Empty dataset");
            shuffle(keys,seed);
            for(int w=0;w<2;w++)try(var r=Files.newBufferedReader(dir.resolve("queries_"+WORK[w]+".txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){Record a=records.get(s);if(a==null){a=new Record();records.put(s,a);}a.freq[w]++;queries[w]++;}
                if(queries[w]==0)throw new IOException("Empty workload");
            }
            System.err.println("rows="+keys.size()+" distinct union="+records.size()+" queries="+Arrays.toString(queries));
        }
        void partition(int P){
            Arrays.fill(positive,0);
            for(int i=0;i<keys.size();i++){Record r=records.get(keys.get(i));r.pid=i/P;for(int w=0;w<2;w++)positive[w]+=r.freq[w];}
        }
    }
    static void u32(OutputStream out,int n)throws IOException{for(int i=0;i<4;i++)out.write(n>>>(8*i));}
    static void header(OutputStream out,int np,int B,String schema)throws IOException{
        byte[] s=schema.getBytes(StandardCharsets.US_ASCII);
        out.write("CMP1".getBytes(StandardCharsets.US_ASCII));u32(out,np);u32(out,B);u32(out,s.length);out.write(s);
    }
    static double pct(long a,long b){return b==0?0:100.0*a/b;}
    static String csv(Object... values){
        StringJoiner s=new StringJoiner(",");
        for(Object v:values)s.add(v instanceof Double d?String.format(Locale.ROOT,"%.9f",d):String.valueOf(v));
        return s.toString();
    }
    static void row(PrintWriter w,Object... values){w.println(csv(values));}
    static PrintWriter writer(Path p)throws IOException{return new PrintWriter(Files.newBufferedWriter(p,StandardCharsets.UTF_8));}
    static String positions(int[] p){StringJoiner s=new StringJoiner(";");for(int i:p)s.add(""+i);return s.toString();}
}
