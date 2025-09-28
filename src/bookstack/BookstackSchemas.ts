import { z } from "zod";

export const tagSchema = z
  .object({
    name: z.string().min(1).describe("Tag key"),
    value: z.string().describe("Tag value"),
  })
  .describe("Bookstack tag definition");

export const tagArraySchema = z
  .array(tagSchema)
  .describe("List of Bookstack tags");

export type TagInput = z.infer<typeof tagSchema>;

export const createIdSchema = (label: string) =>
  z
    .number()
    .int()
    .min(1)
    .describe(label);
