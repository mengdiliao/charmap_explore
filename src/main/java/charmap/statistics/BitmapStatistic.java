package charmap.statistics;

/** Shared transposed bitmap storage and original serialized schema. */
public abstract class BitmapStatistic {
        public final String name,kind;public final int bytes,p,q,k,nw;public final int[] positions;public final long[] post;
        public long ndv,occupied;public final long[] exact=new long[2];
        protected BitmapStatistic(String n,String kind,int b,int p,int q,int k,int nw,int[] positions){
            this.name=n;this.kind=kind;bytes=b;this.p=p;this.q=q;this.k=k;this.nw=nw;this.positions=positions;post=new long[Math.multiplyExact(b*8,nw)];
        }
        public abstract int bit(String s,long h,int j);
        public void add(String s,long h,int pid){for(int j=0;j<k;j++){int b=bit(s,h,j);post[b*nw+pid/64]|=1L<<(pid%64);}}
        public String schema(){String s=name+":"+kind+":"+bytes+":"+p+":"+q+":"+k;if(kind.equals("joint"))for(int x:positions)s+=":"+x;return s;}
    }
