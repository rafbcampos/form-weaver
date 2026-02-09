import { Interview } from "./components/Interview";
import type { InterviewSchema } from "./types/schema";
import userProfileSchema from "../../schemas/user_profile.json";

const schema = userProfileSchema as InterviewSchema;

export function App() {
  return <Interview schema={schema} />;
}
