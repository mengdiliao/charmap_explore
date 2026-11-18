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

    /** Exact projected sequence, including symbol 128 for missing positions. */
    public static String extractCharacters(String s,int[] positions) {
        char[] result=new char[positions.length];
        for(int i=0;i<positions.length;i++)result[i]=(char)ch(s,positions[i]);
        return new String(result);
    }

    /** Inverse of the fixed-length base-256 pair / base-257 tuple encoding. */
    public static String decodeToken(long token,int length,int base) {
        char[] result=new char[length];
        for(int i=length-1;i>=0;i--){result[i]=(char)(token%base);token/=base;}
        return new String(result);
    }
}
