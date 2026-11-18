package charmap;
import charmap.core.*;
import charmap.evaluation.Evaluator;
import charmap.statistics.BloomFilter;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CorrectnessTest {
    @Test void asciiPositionsAndMissing() {
        assertEquals(97, CharacterEncoding.ch("abc",0));
        assertEquals(99, CharacterEncoding.ch("abc",-1));
        assertEquals(128, CharacterEncoding.ch("a",1));
        assertEquals(128, CharacterEncoding.ch("",-1));
        assertEquals(97*257L+128, CharacterEncoding.token("a", new int[]{0,1}));
        assertEquals(97*256L+99,CharacterEncoding.pair("abc",0,-1));
    }
    @Test void referenceBloomK() {
        assertEquals(1,BloomFilter.optimalK(8000,512));
        assertEquals(3,BloomFilter.optimalK(500,256));
    }
    @Test void unsignedBucketAndHash() {
        assertEquals(5,HashUtils.bucket(-1L,10));
        assertEquals(0,HashUtils.bucket(0L,4096));
        assertEquals(0,HashUtils.mix(0L));
        assertEquals(HashUtils.hash("abc"),HashUtils.hash(new String("abc")));
    }
    @Test void legacyShuffle() {
        var a=new ArrayList<>(List.of("0","1","2","3","4","5","6"));
        PartitionLayout.shuffle(a,55);
        assertEquals(List.of("3","0","5","2","6","4","1"),a);
        var b=new ArrayList<>(List.of("0","1","2","3","4","5","6","7"));
        PartitionLayout.shuffle(b,55);
        assertEquals(List.of("2","5","4","6","1","3","7","0"),b);
    }
    @Test void membersNeverPrunedAndQueriesWeighted(@TempDir Path dir)throws Exception {
        // Synthetic correctness fixture, deliberately includes empty keys,
        // short strings, repeated queries and a partial final partition.
        Files.writeString(dir.resolve("dataset.txt"),"abc\nab\nx\n\nz\n");
        Files.writeString(dir.resolve("queries_uniform.txt"),"abc\nabc\nab\nx\n\nz\nabsent\n");
        Files.writeString(dir.resolve("queries_zipf.txt"),"\n\n\nx\nz\nother\n");
        Path candidates=dir.resolve("designs.tsv");
        Files.writeString(candidates,"ReferenceJointCM\t0\t1\t-2\t-1\nShortTuple\t0\t15\n");
        Path out=dir.resolve("out");
        new Evaluator(new Dataset(dir,55),2,32,out,"position").run(candidates);
        List<String> lines=Files.readAllLines(out.resolve("results.csv"));
        assertEquals(9,lines.size()); // 4 algorithms x 2 workloads + header
        String[] header=lines.get(0).split(",",-1);
        List<String> cols=Arrays.asList(header);
        for(String line:lines.subList(1,lines.size())){
            String[] row=line.split(",",-1);
            assertEquals(header.length,row.length);
            assertEquals("0",row[cols.indexOf("false_negatives")]);
            assertEquals(row[0].equals("uniform")?"7":"6",row[cols.indexOf("queries")]);
            assertEquals(row[0].equals("uniform")?"6":"5",row[cols.indexOf("oracle_retained")]);
            long ret=Long.parseLong(row[cols.indexOf("retained")]);
            assertTrue(ret>=Long.parseLong(row[cols.indexOf("oracle_retained")]));
        }
        assertTrue(Files.size(out.resolve("ReferenceJointCM.bin"))>3*32);
    }
}
