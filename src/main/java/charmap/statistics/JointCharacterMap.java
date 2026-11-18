package charmap.statistics;

import charmap.encoding.CharacterEncoding;
import charmap.hashing.HashUtils;

/** Single-hash Bloom over the projected character sequence. */
public final class JointCharacterMap extends BitmapStatistic {
    public JointCharacterMap(String name,String kind,int bytes,int p,int q,int nw,int[] positions){
        super(name,kind,bytes,p,q,1,nw,positions);
    }

    public long projectedHash(String s){
        long h=HashUtils.FNV_OFFSET;
        if(kind.equals("pair")){
            h=HashUtils.fnv1aStep(h,CharacterEncoding.ch(s,p));
            h=HashUtils.fnv1aStep(h,CharacterEncoding.ch(s,q));
        }else{
            for(int position:positions)h=HashUtils.fnv1aStep(h,CharacterEncoding.ch(s,position));
        }
        return h;
    }

    @Override public int bit(String s,long h,int j){
        return HashUtils.hashToBit(projectedHash(s),j,bytes*8);
    }

    @Override public String schema(){return super.schema()+":hash="+HashUtils.VERSION;}
}
