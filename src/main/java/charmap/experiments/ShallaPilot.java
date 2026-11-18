package charmap.experiments;
import charmap.data.DatasetLoader;
import charmap.evaluation.*;
import java.nio.file.Path;
public final class ShallaPilot {
 public static void main(String[] args)throws Exception {
 if(args.length!=3)throw new IllegalArgumentException("data_dir output_dir budget");int b=Integer.parseInt(args[2]);if(b!=32&&b!=64&&b!=128&&b!=256)throw new IllegalArgumentException("budget");new Evaluator(DatasetLoader.load(Path.of(args[0]),55),500,b,Path.of(args[1]),"pilot").run(null);
 }
}
