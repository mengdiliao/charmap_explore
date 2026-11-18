package charmap.statistics;
import charmap.encoding.CharacterEncoding;
public final class CharacterMap extends BitmapStatistic {
    public CharacterMap(String name,int bytes,int p,int nw){super(name,"pos",bytes,p,0,1,nw,null);}
    @Override public int bit(String s,long h,int j){return CharacterEncoding.ch(s,p)%128;}
}
