import { Box, Text } from "ink";
import { colors } from "../utils/colors.ts";
import { REPL } from "./REPL.tsx";

interface AppProps {
  apiKey: string;
  model: string;
}

export function App({ apiKey, model }: AppProps) {
  return (
    <Box flexDirection="column">
      <Box marginBottom={1} paddingX={1}>
        <Text>{colors.header("kai")}</Text>
        <Text>{colors.muted(` (${model})`)}</Text>
      </Box>
      <Box paddingX={1} marginBottom={1}>
        <Text>{colors.muted(`Type a message to chat. "exit" to quit.`)}</Text>
      </Box>
      <REPL apiKey={apiKey} model={model} />
    </Box>
  );
}
