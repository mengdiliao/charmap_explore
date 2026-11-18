package charmap.data;

import java.util.ArrayList;
import java.util.HashMap;

/** In-memory keys, query multiplicities and partition membership; no file I/O. */
public final class LoadedData {
    public static final String[] WORK={"uniform","zipf"};
    public static final class Record {
        public int pid=-1;public final long[] freq=new long[2];
    }
    public final ArrayList<String> keys=new ArrayList<>();
    public final HashMap<String,Record> records=new HashMap<>(4_000_000);
    public final long[] queries=new long[2],positive=new long[2];public int maxlen;
    LoadedData() {}
}
