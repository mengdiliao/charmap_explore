package charmap.data;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/** Reads prepared input files and preserves original query frequencies and shuffle. */
public final class DatasetLoader {
    private DatasetLoader() {}
    public static LoadedData load(Path dir,long seed)throws IOException{
        LoadedData data=new LoadedData();
        var keys=data.keys;
        var records=data.records;
        var queries=data.queries;
            try(var r=Files.newBufferedReader(dir.resolve("dataset.txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){if(records.putIfAbsent(s,new LoadedData.Record())!=null)throw new IOException("Duplicate stored key");keys.add(s);data.maxlen=Math.max(data.maxlen,s.length());}
            }
            if(keys.isEmpty())throw new IOException("Empty dataset");
            PartitionLayout.shuffle(keys,seed);
            for(int w=0;w<2;w++)try(var r=Files.newBufferedReader(dir.resolve("queries_"+LoadedData.WORK[w]+".txt"),StandardCharsets.US_ASCII)){
                String s;while((s=r.readLine())!=null){LoadedData.Record a=records.get(s);if(a==null){a=new LoadedData.Record();records.put(s,a);}a.freq[w]++;queries[w]++;}
                if(queries[w]==0)throw new IOException("Empty workload");
            }
            System.err.println("rows="+keys.size()+" distinct union="+records.size()+" queries="+Arrays.toString(queries));
        return data;
    }
}
