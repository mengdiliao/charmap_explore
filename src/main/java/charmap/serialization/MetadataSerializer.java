package charmap.serialization;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import charmap.statistics.BitmapStatistic;
public final class MetadataSerializer {
    public static void u32(OutputStream out,int n)throws IOException{for(int i=0;i<4;i++)out.write(n>>>(8*i));}
    public static void header(OutputStream out,int np,int B,String schema)throws IOException{
        byte[] s=schema.getBytes(StandardCharsets.US_ASCII);
        out.write("CMP1".getBytes(StandardCharsets.US_ASCII));u32(out,np);u32(out,B);u32(out,s.length);out.write(s);
    }
    public static long write(Path path,int np,int nw,int B,String name,BitmapStatistic[] cs)throws IOException{
        String schema=name;int b=0;for(BitmapStatistic c:cs){schema+=";"+c.schema();b+=c.bytes;}
        if(b>B||b==0)throw new IOException("budget");
        try(var f=new BufferedOutputStream(Files.newOutputStream(path))){
            header(f,np,b,schema);
            for(int pid=0;pid<np;pid++)for(BitmapStatistic c:cs)for(int j=0;j<c.bytes;j++){
                int v=0;for(int bit=0;bit<8;bit++)if((c.post[(j*8+bit)*nw+pid/64]&(1L<<(pid%64)))!=0)v|=1<<bit;f.write(v);}
        }
        long meta=Files.size(path);if(meta!=16+schema.length()+(long)np*b)throw new IOException("serialized size");return meta;
    }

}
