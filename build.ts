// build.ts
import { $ } from "bun";

const targets = [
  { target: "bun-linux-x64", output: "dist/my-cli-linux-x64" },
  { target: "bun-linux-arm64", output: "dist/my-cli-linux-arm64" },
  { target: "bun-darwin-x64", output: "dist/my-cli-macos-x64" },
  { target: "bun-darwin-arm64", output: "dist/my-cli-macos-arm64" },
  { target: "bun-windows-x64", output: "dist/my-cli-windows-x64.exe" },
];

await $`mkdir -p dist`;

const allTargets = process.argv.includes("--all-targets");
const buildTargets = allTargets ? targets : [targets[0]]; // local: just linux x64

for (const { target, output } of buildTargets) {
  console.log(`Building ${target}...`);
  await $`bun build src/index.ts --compile --target=${target} --outfile=${output}`;
  console.log(`  ✓ ${output}`);
}
