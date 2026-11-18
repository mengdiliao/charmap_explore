package charmap.core;
import java.util.*;
public final class PartitionLayout {
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
    public static void shuffle(List<String> a,long seed){
        MT64 rng=new MT64(seed);int n=a.size(),i=1;
        if(n<2)return;
        if(n%2==0){Collections.swap(a,1,(int)rng.below(2));i++;}
        while(i<n){long b=i+1L;long x=rng.below(b*(b+1));Collections.swap(a,i,(int)(x/(b+1)));i++;
            Collections.swap(a,i,(int)(x%(b+1)));i++;}
    }
    public static void partition(Dataset data,int P){
            Arrays.fill(data.positive,0);
            for(int i=0;i<data.keys.size();i++){Dataset.Record r=data.records.get(data.keys.get(i));r.pid=i/P;for(int w=0;w<2;w++)data.positive[w]+=r.freq[w];}
        }

}
