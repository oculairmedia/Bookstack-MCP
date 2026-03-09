import { z } from "zod";
export declare const tagSchema: any;
export declare const tagArraySchema: any;
export type TagInput = z.infer<typeof tagSchema>;
export declare const createIdSchema: (label: string) => any;
