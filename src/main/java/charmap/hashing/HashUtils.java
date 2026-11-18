package charmap.hashing;

/** Unified 64-bit FNV-1a, one SplitMix64-style finalizer, unsigned modulo. */
public final class HashUtils {
    public static final String VERSION="fnv1a-mix-v1";
    public static final long FNV_OFFSET=0xcbf29ce484222325L;
    private static final long FNV_PRIME=1099511628211L;
    private static final long HASH_STEP=0x9e3779b97f4a7c15L;

    private HashUtils() {}

    public static long fnv1aStep(long h,int symbol) {
        return (h ^ symbol)*FNV_PRIME;
    }

    public static long fnv1a(String s) {
        long h=FNV_OFFSET;
        for(int i=0;i<s.length();i++)h=fnv1aStep(h,s.charAt(i));
        return h;
    }

    public static long mix(long x) {
        x=(x^(x>>>30))*0xbf58476d1ce4e5b9L;
        x=(x^(x>>>27))*0x94d049bb133111ebL;
        return x^(x>>>31);
    }

    public static int hashToBit(long rawHash,int j,int bitmapSize) {
        return (int)Long.remainderUnsigned(mix(rawHash+j*HASH_STEP),bitmapSize);
    }
}
