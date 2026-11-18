package charmap.encoding;

public final class CharacterEncoding {
    public static final int[] REF={0,1,-2,-1};
    public static int ch(String s,int p) {
        int i=p>=0?p:s.length()+p;
        return i<0||i>=s.length()?128:s.charAt(i);
    }
    public static long token(String s,int[] pos) {
        long v=0;for(int p:pos)v=v*257+ch(s,p);return v;
    }
    public static long pair(String s,int p,int q){return ch(s,p)*256L+ch(s,q);}

}
