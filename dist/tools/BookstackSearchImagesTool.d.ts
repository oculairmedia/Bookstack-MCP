import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type SearchImagesInput = z.infer<typeof schema>;
declare class BookstackSearchImagesTool extends BookstackTool<SearchImagesInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: SearchImagesInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
    private buildResponse;
}
export default BookstackSearchImagesTool;
