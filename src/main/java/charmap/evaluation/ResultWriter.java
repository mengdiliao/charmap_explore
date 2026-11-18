package charmap.evaluation;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public final class ResultWriter {
    public static double pct(long a,long b){return b==0?0:100.0*a/b;}
    public static String csv(Object... values){
        StringJoiner s=new StringJoiner(",");
        for(Object v:values)s.add(v instanceof Double d?String.format(Locale.ROOT,"%.9f",d):String.valueOf(v));
        return s.toString();
    }
    public static void row(PrintWriter w,Object... values){w.println(csv(values));}
    public static PrintWriter writer(Path p)throws IOException{return new PrintWriter(Files.newBufferedWriter(p,StandardCharsets.UTF_8));}
    public static String positions(int[] p){StringJoiner s=new StringJoiner(";");for(int i:p)s.add(""+i);return s.toString();}

}
