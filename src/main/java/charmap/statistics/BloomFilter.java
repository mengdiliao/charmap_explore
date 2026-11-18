package charmap.statistics;
import charmap.core.HashUtils;
public final class BloomFilter extends BitmapStatistic {
    public BloomFilter(String name,int bytes,int k,int nw){super(name,"bloom",bytes,0,0,k,nw,null);}
    public static int optimalK(int P,int B){
        int k=1;double best=1;
        for(int i=1;i<=16;i++){double f=Math.pow(1-Math.exp(-(double)i*P/(B*8)),i);if(f<best){k=i;best=f;}}
        return k;
    }
    @Override public int bit(String s,long h,int j){return HashUtils.bucket(HashUtils.mix(h+j*0x9e3779b97f4a7c15L),bytes*8);}
}
