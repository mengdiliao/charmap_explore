package charmap;
import charmap.data.DatasetLoader;
import charmap.data.PartitionLayout;
import charmap.encoding.CharacterEncoding;
import charmap.hashing.HashUtils;
import charmap.evaluation.Evaluator;
import charmap.statistics.BloomFilter;
import charmap.statistics.JointCharacterMap;

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
    @Test void unifiedHashKnownVectors() {
        assertEquals(0xcbf29ce484222325L,HashUtils.fnv1a(""));
        assertEquals(0xe71fa2190541574bL,HashUtils.fnv1a("abc"));
        assertEquals(0L,HashUtils.mix(0L));
        assertEquals((int)Long.remainderUnsigned(HashUtils.mix(HashUtils.fnv1a("abc")),4096),
                     HashUtils.hashToBit(HashUtils.fnv1a("abc"),0,4096));
        assertEquals((int)Long.remainderUnsigned(HashUtils.mix(HashUtils.fnv1a("abc")+0x9e3779b97f4a7c15L),1000),
                     HashUtils.hashToBit(HashUtils.fnv1a("abc"),1,1000));
        for(int i=0;i<16;i++){
            int bit=HashUtils.hashToBit(HashUtils.fnv1a("abc"),i,1000);
            assertTrue(bit>=0&&bit<1000);
        }
    }
    @Test void identicalProjectedAndFullInputMapping() {
        for(String key:List.of("www.example.com","a","","ab","a\0b","abc.def")){
            for(int[] pos:List.of(new int[]{0,1,-2,-1},new int[]{0,15},new int[]{0,1,2,-3,-2,-1})){
                var joint=new JointCharacterMap("joint","joint",512,0,0,1,pos);
                var bloom=new BloomFilter("bloom",512,1,1);
                String token=CharacterEncoding.extractCharacters(key,pos);
                assertEquals(token,CharacterEncoding.decodeToken(CharacterEncoding.token(key,pos),pos.length,257));
                assertEquals(HashUtils.fnv1a(token),joint.projectedHash(key));
                assertEquals(bloom.bit(token,HashUtils.fnv1a(token),0),joint.bit(key,HashUtils.fnv1a(key),0));
                assertTrue(joint.schema().contains(HashUtils.VERSION));
                assertTrue(bloom.schema().contains(HashUtils.VERSION));
            }
            var pair=new JointCharacterMap("pair","pair",16,0,-1,1,null);
            String token=CharacterEncoding.extractCharacters(key,new int[]{0,-1});
            assertEquals(token,CharacterEncoding.decodeToken(CharacterEncoding.pair(key,0,-1),2,256));
            assertEquals(HashUtils.hashToBit(HashUtils.fnv1a(token),0,128),pair.bit(key,0,0));
        }
        assertEquals("\u0080",CharacterEncoding.extractCharacters("",new int[]{0}));
        assertNotEquals(CharacterEncoding.extractCharacters("",new int[]{0}),CharacterEncoding.extractCharacters("\0",new int[]{0}));
    }
    @Test void legacyShuffle() {
        var a=new ArrayList<>(List.of("0","1","2","3","4","5","6"));
        PartitionLayout.shuffle(a,55);
        assertEquals(List.of("3","0","5","2","6","4","1"),a);
        var b=new ArrayList<>(List.of("0","1","2","3","4","5","6","7"));
        PartitionLayout.shuffle(b,55);
        assertEquals(List.of("2","5","4","6","1","3","7","0"),b);
    }
    @Test void preparedFilesAndQueryMultiplicity(@TempDir Path dir)throws Exception {
        Files.writeString(dir.resolve("dataset.txt"),"abc\nxyz\n");
        Files.writeString(dir.resolve("queries_uniform.txt"),"abc\nabc\nabsent\n");
        Files.writeString(dir.resolve("queries_zipf.txt"),"xyz\nxyz\nxyz\nabsent\n");
        var data=DatasetLoader.load(dir,55);
        assertEquals(2,data.keys.size());
        assertEquals(3,data.records.size());
        assertArrayEquals(new long[]{3,4},data.queries);
        assertArrayEquals(new long[]{2,0},data.records.get("abc").freq);
        assertArrayEquals(new long[]{0,3},data.records.get("xyz").freq);
        assertEquals(-1,data.records.get("absent").pid);
        PartitionLayout.partition(data,1);
        assertArrayEquals(new long[]{2,3},data.positive);
        assertEquals(-1,data.records.get("absent").pid);
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
        new Evaluator(DatasetLoader.load(dir,55),2,32,out,"position").run(candidates);
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
            if(row[1].equals("OptimizedBloom")) {
                assertEquals(5.0/3,Double.parseDouble(row[cols.indexOf("mean_token_ndv")]),1e-9);
                assertTrue(Double.parseDouble(row[cols.indexOf("mean_saturation_pct")])>0);
                assertTrue(Integer.parseInt(row[cols.indexOf("bloom_k")])>1);
                assertEquals("",row[cols.indexOf("collision_excess_pct")]);
            }
            long ret=Long.parseLong(row[cols.indexOf("retained")]);
            assertTrue(ret>=Long.parseLong(row[cols.indexOf("oracle_retained")]));
        }
        assertTrue(Files.size(out.resolve("ReferenceJointCM.bin"))>3*32);
    }
    @Test void singleHashBloomDiagnostics(@TempDir Path dir)throws Exception {
        // Force two distinct full keys into the same bit; no projection involved.
        Map<Integer,String> seen=new HashMap<>();
        String a=null,b=null;
        for(int i=0;i<=256;i++){
            String key="key"+i;
            int bit=HashUtils.hashToBit(HashUtils.fnv1a(key),0,256);
            String prior=seen.putIfAbsent(bit,key);
            if(prior!=null){a=prior;b=key;break;}
        }
        assertNotNull(a);
        assertNotNull(b);
        Files.writeString(dir.resolve("dataset.txt"),a+"\n"+b+"\n");
        Files.writeString(dir.resolve("queries_uniform.txt"),a+"\nabsent\n");
        Files.writeString(dir.resolve("queries_zipf.txt"),b+"\nabsent\n");
        Path candidates=dir.resolve("designs.tsv");
        Files.writeString(candidates,"ReferenceJointCM\t0\t-1\n");
        Path out=dir.resolve("out");
        new Evaluator(DatasetLoader.load(dir,55),500,32,out,"position").run(candidates);
        List<String> lines=Files.readAllLines(out.resolve("results.csv"));
        List<String> cols=Arrays.asList(lines.get(0).split(",",-1));
        int count=0;
        for(String line:lines.subList(1,lines.size())){
            String[] row=line.split(",",-1);
            if(!row[1].equals("OptimizedBloom"))continue;
            count++;
            assertEquals("1",row[cols.indexOf("bloom_k")]);
            assertEquals(2.0,Double.parseDouble(row[cols.indexOf("mean_token_ndv")]),1e-9);
            assertEquals(100.0/256,Double.parseDouble(row[cols.indexOf("mean_saturation_pct")]),1e-9);
            assertEquals(50.0,Double.parseDouble(row[cols.indexOf("collision_excess_pct")]),1e-9);
            assertEquals("",row[cols.indexOf("exact_joint_pruning_pct")]);
            assertEquals("0",row[cols.indexOf("false_negatives")]);
        }
        assertEquals(2,count);
    }

}
