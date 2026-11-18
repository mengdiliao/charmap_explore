package charmap;
import java.nio.file.Path;
public final class PartitionSensitivity {
 public static void main(String[] args)throws Exception {
 if(args.length!=4)throw new IllegalArgumentException("data_dir output_dir partition_size budget");new Evaluator(new Core.Data(Path.of(args[0]),55),Integer.parseInt(args[2]),Integer.parseInt(args[3]),Path.of(args[1]),"sensitivity").run(null);
 }
}
