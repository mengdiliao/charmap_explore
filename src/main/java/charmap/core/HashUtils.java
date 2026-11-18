package charmap.core;

public final class HashUtils {
    public static long mix(long x) {
        x=(x^(x>>>30))*0xbf58476d1ce4e5b9L;
        x=(x^(x>>>27))*0x94d049bb133111ebL;
        return x^(x>>>31);
    }
    public static long hash(String s) {
        long h=0xcbf29ce484222325L;
        for(int i=0;i<s.length();i++) {h^=s.charAt(i);h*=1099511628211L;}
        return mix(h);
    }
    public static int bucket(long x,int m){return (int)Long.remainderUnsigned(x,m);}

}
