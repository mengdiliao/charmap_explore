package charmap.statistics;
import charmap.encoding.CharacterEncoding;
import charmap.hashing.HashUtils;
/** Preserve distinct legacy pair and general tuple encodings. */
public final class JointCharacterMap extends BitmapStatistic {
    public JointCharacterMap(String name,String kind,int bytes,int p,int q,int nw,int[] positions){super(name,kind,bytes,p,q,1,nw,positions);}
    @Override public int bit(String s,long h,int j){
        return HashUtils.bucket(HashUtils.mix(kind.equals("pair")?CharacterEncoding.pair(s,p,q):CharacterEncoding.token(s,positions)),bytes*8);
    }
}
