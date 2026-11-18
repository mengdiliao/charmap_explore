package charmap.statistics;
public final class LengthMap extends BitmapStatistic {
    public LengthMap(String name,int bytes,int nw){super(name,"len",bytes,0,0,1,nw,null);}
    @Override public int bit(String s,long h,int j){return Math.min(s.length(),bytes*8-1);}
}
