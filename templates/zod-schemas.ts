/**
 * Zod Schemas: Shared validation for frontend and backend
 * Usage:
 *   import { userSchema, paginatedResponse } from "@/lib/schemas";
 *   const user = userSchema.parse(data);
 *   type User = z.infer<typeof userSchema>;
 */
import { z } from "zod";

// ---- Primitives ----

export const emailSchema = z.string().email("Invalid email").toLowerCase().trim();
export const passwordSchema = z.string().min(8, "Min 8 characters").max(128);
export const idSchema = z.string().uuid("Invalid ID");
export const slugSchema = z.string().regex(/^[a-z0-9-]+$/, "Lowercase, numbers, hyphens only");

// ---- User ----

export const userSchema = z.object({
    id: idSchema,
    email: emailSchema,
    name: z.string().min(1, "Name required").max(100),
    avatar: z.string().url().nullable().default(null),
    role: z.enum(["user", "admin", "moderator"]).default("user"),
    createdAt: z.coerce.date(),
});

export const createUserSchema = userSchema.omit({ id: true, createdAt: true });
export const updateUserSchema = createUserSchema.partial();

export type User = z.infer<typeof userSchema>;
export type CreateUser = z.infer<typeof createUserSchema>;
export type UpdateUser = z.infer<typeof updateUserSchema>;

// ---- Pagination ----

export const paginationSchema = z.object({
    page: z.coerce.number().int().min(1).default(1),
    limit: z.coerce.number().int().min(1).max(100).default(20),
    sort: z.string().optional(),
    order: z.enum(["asc", "desc"]).default("desc"),
});

export type PaginationParams = z.infer<typeof paginationSchema>;

// ---- API Response ----

export function apiResponseSchema<T extends z.ZodType>(dataSchema: T) {
    return z.object({
        data: dataSchema.nullable(),
        error: z
            .object({
                code: z.string(),
                message: z.string(),
                field: z.string().optional(),
            })
            .nullable(),
        meta: z.object({
            timestamp: z.string(),
            requestId: z.string(),
        }),
    });
}

export function paginatedResponseSchema<T extends z.ZodType>(itemSchema: T) {
    return apiResponseSchema(
        z.object({
            items: z.array(itemSchema),
            total: z.number(),
            page: z.number(),
            limit: z.number(),
            pages: z.number(),
        })
    );
}

// ---- Contact / Form ----

export const contactFormSchema = z.object({
    name: z.string().min(1, "Name required").max(100),
    email: emailSchema,
    message: z.string().min(10, "Min 10 characters").max(2000),
    phone: z.string().optional(),
});

export type ContactForm = z.infer<typeof contactFormSchema>;
