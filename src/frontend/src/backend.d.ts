import type { Principal } from "@icp-sdk/core/principal";
export interface Some<T> {
    __kind__: "Some";
    value: T;
}
export interface None {
    __kind__: "None";
}
export type Option<T> = Some<T> | None;
export interface BlogPost {
    id: bigint;
    title: string;
    created: Time;
    content: string;
    author: string;
}
export type Time = bigint;
export interface YouTubeVideo {
    id: bigint;
    url: string;
    title: string;
    description: string;
}
export interface Note {
    id: bigint;
    title: string;
    created: Time;
    content: string;
    category: NoteCategory;
}
export enum NoteCategory {
    adhd = "adhd",
    dyslexia = "dyslexia",
    autism = "autism",
    general = "general"
}
export enum UserRole {
    admin = "admin",
    user = "user",
    guest = "guest"
}
export interface backendInterface {
    assignCallerUserRole(user: Principal, role: UserRole): Promise<void>;
    createBlog(title: string, content: string, author: string): Promise<BlogPost>;
    createNote(title: string, content: string, category: NoteCategory): Promise<Note>;
    createVideo(title: string, description: string, url: string): Promise<YouTubeVideo>;
    deleteBlog(id: bigint): Promise<void>;
    deleteNote(id: bigint): Promise<void>;
    deleteVideo(id: bigint): Promise<void>;
    getAllBlogs(): Promise<Array<BlogPost>>;
    getAllNotes(): Promise<Array<Note>>;
    getAllVideos(): Promise<Array<YouTubeVideo>>;
    getBlog(id: bigint): Promise<BlogPost | null>;
    getCallerUserRole(): Promise<UserRole>;
    getNote(id: bigint): Promise<Note | null>;
    getNotesByCategory(category: NoteCategory): Promise<Array<Note>>;
    getVideo(id: bigint): Promise<YouTubeVideo | null>;
    isCallerAdmin(): Promise<boolean>;
    updateBlog(id: bigint, title: string, content: string, author: string): Promise<void>;
    updateNote(id: bigint, title: string, content: string, category: NoteCategory): Promise<void>;
    updateVideo(id: bigint, title: string, description: string, url: string): Promise<void>;
}
