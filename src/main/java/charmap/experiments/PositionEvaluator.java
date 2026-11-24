package charmap.experiments;
import charmap.data.DatasetLoader;
import charmap.evaluation.Evaluator;
import java.nio.file.Path;

public final class PositionEvaluator {
    public static void main(String[] args)throws Exception {
        if(args.length==6){
            new Evaluator(DatasetLoader.load(Path.of(args[0]),Long.parseLong(args[5])),
                Integer.parseInt(args[2]),Integer.parseInt(args[3]),Path.of(args[1]),"position").run(Path.of(args[4]));
        }else if(args.length==8){
            new Evaluator(DatasetLoader.loadSelected(Path.of(args[0]),Path.of(args[1]),args[2],Long.parseLong(args[7])),
                Integer.parseInt(args[4]),Integer.parseInt(args[5]),Path.of(args[3]),"position").run(Path.of(args[6]));
        }else throw new IllegalArgumentException("data_dir output_dir partition_size budget candidates.tsv seed OR dataset_file query_file workload output_dir partition_size budget candidates.tsv seed");
    }
}
