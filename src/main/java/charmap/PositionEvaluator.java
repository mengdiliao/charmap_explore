package charmap;
import java.nio.file.Path;
public final class PositionEvaluator {
 public static void main(String[] args)throws Exception {
 if(args.length!=6)throw new IllegalArgumentException("data_dir output_dir partition_size budget candidates.tsv seed");new Evaluator(new Core.Data(Path.of(args[0]),Long.parseLong(args[5])),Integer.parseInt(args[2]),Integer.parseInt(args[3]),Path.of(args[1]),"position").run(Path.of(args[4]));
 }
}
