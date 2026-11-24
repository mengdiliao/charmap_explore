package charmap.data;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/** Reads prepared input files and preserves original query frequencies and shuffle. */
public final class DatasetLoader {
    private DatasetLoader() {}

    private static LoadedData stored(Path dataset,long seed)throws IOException {
        LoadedData data=new LoadedData();
        try(var r=Files.newBufferedReader(dataset,StandardCharsets.US_ASCII)){
            String s;while((s=r.readLine())!=null){
                if(data.records.putIfAbsent(s,new LoadedData.Record())!=null)throw new IOException("Duplicate stored key");
                data.keys.add(s);data.maxlen=Math.max(data.maxlen,s.length());
            }
        }
        if(data.keys.isEmpty())throw new IOException("Empty dataset");
        PartitionLayout.shuffle(data.keys,seed);
        return data;
    }
    private static void readWorkload(LoadedData data,Path query,int w)throws IOException {
        try(var r=Files.newBufferedReader(query,StandardCharsets.US_ASCII)){
            String s;while((s=r.readLine())!=null){
                LoadedData.Record a=data.records.get(s);
                if(a==null){a=new LoadedData.Record();data.records.put(s,a);}
                a.freq[w]++;data.queries[w]++;
            }
        }
        if(data.queries[w]==0)throw new IOException("Empty workload");
    }
    private static void describe(LoadedData data) {
        System.err.println("rows="+data.keys.size()+" distinct union="+data.records.size()+" queries="+Arrays.toString(data.queries));
    }
    public static LoadedData load(Path dir,long seed)throws IOException{
        LoadedData data=stored(dir.resolve("dataset.txt"),seed);
        for(int w=0;w<2;w++)readWorkload(data,dir.resolve("queries_"+LoadedData.WORK[w]+".txt"),w);
        describe(data);
        return data;
    }
    /** Read exactly one selected full workload, retaining its original workload index. */
    public static LoadedData loadSelected(Path dataset,Path query,String workload,long seed)throws IOException {
        int w=switch(workload){case "uniform" -> 0;case "zipf" -> 1;default -> throw new IllegalArgumentException("Unknown workload: "+workload);};
        LoadedData data=stored(dataset,seed);
        readWorkload(data,query,w);
        describe(data);
        return data;
    }
}
