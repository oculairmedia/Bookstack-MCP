import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type UpdateChapterInput = z.infer<typeof schema>;
declare class BookstackUpdateChapterTool extends BookstackTool<UpdateChapterInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: UpdateChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateChapterTool;
