package charmap.core;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public final class Dataset {
    public static final String[] WORK={"uniform","zipf"};
    public static final class Record {
        public int pid=-1;public final long[] freq=new long[2];
    }
        public final ArrayList<String> keys=new ArrayList<>();
        public final HashMap<String,Record> records=new HashMap<>(4_000_000);
        public final long[] queries=new long[2],positive=new long[2];public int maxlen;
        public Dataset(Path dir,long seed)throws IOException{
            try(var r=Files.newBufferedReader(dir.resolve("dataset.txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){if(records.putIfAbsent(s,new Record())!=null)throw new IOException("Duplicate stored key");keys.add(s);maxlen=Math.max(maxlen,s.length());}
            }
            if(keys.isEmpty())throw new IOException("Empty dataset");
            PartitionLayout.shuffle(keys,seed);
            for(int w=0;w<2;w++)try(var r=Files.newBufferedReader(dir.resolve("queries_"+WORK[w]+".txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){Record a=records.get(s);if(a==null){a=new Record();records.put(s,a);}a.freq[w]++;queries[w]++;}
                if(queries[w]==0)throw new IOException("Empty workload");
            }
            System.err.println("rows="+keys.size()+" distinct union="+records.size()+" queries="+Arrays.toString(queries));
        }
        public void partition(int P){PartitionLayout.partition(this,P);}

}
