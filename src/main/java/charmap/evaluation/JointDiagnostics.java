package charmap.evaluation;
import java.util.*;
import charmap.encoding.CharacterEncoding;
import charmap.data.LoadedData;
import charmap.statistics.BitmapStatistic;
final class JointDiagnostics {
    static void collect(BitmapStatistic c,LoadedData d,int P){
        if(c.kind.equals("bloom")) {
            // DatasetLoader rejects duplicate stored keys. Each key belongs to one partition.
            c.ndv=d.keys.size();
            for(long x:c.post)c.occupied+=Long.bitCount(x);
            return;
        }
        if(!c.kind.equals("joint"))return;
        HashMap<Long,long[]> q=new HashMap<>();
        for(var e:d.records.entrySet()){var f=e.getValue().freq;if(f[0]==0&&f[1]==0)continue;long t=CharacterEncoding.token(e.getKey(),c.positions);long[] a=q.computeIfAbsent(t,x->new long[2]);a[0]+=f[0];a[1]+=f[1];}
        long[] tokens=new long[P];
        for(int i=0;i<d.keys.size();i+=P){int n=Math.min(P,d.keys.size()-i);for(int j=0;j<n;j++)tokens[j]=CharacterEncoding.token(d.keys.get(i+j),c.positions);Arrays.sort(tokens,0,n);
            for(int j=0;j<n;j++)if(j==0||tokens[j]!=tokens[j-1]){c.ndv++;long[] f=q.get(tokens[j]);if(f!=null){c.exact[0]+=f[0];c.exact[1]+=f[1];}}}
        for(long x:c.post)c.occupied+=Long.bitCount(x);
    }

}
