//
// September 2020, Lewis Gaul
//

// use std::fs;
use std::error::Error;

use yaml_rust::YamlLoader;

static YAML: &str = r#"
help: |
  Example CLI!

  Run the app by simply passing in no arguments...
command: "run"

subtree:
  - keyword: venv
    help: "Set up the project's virtual environment"
"#;

fn main() -> Result<(), Box<dyn Error>> {
    // Read in CLI schema.
    let yaml = YamlLoader::load_from_str(YAML)?;
    dbg!(yaml);

    // Parse args.
    let args = clap::App::new("myapp").get_matches();
    dbg!(args);

    Ok(())
}
