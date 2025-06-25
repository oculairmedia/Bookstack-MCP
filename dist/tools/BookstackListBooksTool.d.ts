import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ListBooksInput {
    offset?: string;
    count?: string;
}
declare class BookstackListBooksTool extends MCPTool<ListBooksInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        offset: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        count: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
    };
    execute(input: ListBooksInput): Promise<{
        content: {
            type: string;
            text: string;
        }[];
        jsonrpc?: undefined;
        method?: undefined;
        id?: undefined;
        params?: undefined;
        error?: undefined;
    } | {
        jsonrpc: string;
        method: string;
        id: number;
        params: {
            offset: string | undefined;
            count: string | undefined;
        };
        error: {
            code: number;
            message: any;
            data: {
                type: string;
                content: {
                    type: string;
                    text: string;
                }[];
            };
        };
        content?: undefined;
    }>;
}
export default BookstackListBooksTool;
