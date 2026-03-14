import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NoteCategory } from "../backend.d";
import type { BlogPost, Note, YouTubeVideo } from "../backend.d";
import { useActor } from "./useActor";

export type { Note, YouTubeVideo, BlogPost };
export { NoteCategory };

export function useIsAdmin() {
  const { actor, isFetching } = useActor();
  return useQuery({
    queryKey: ["isAdmin"],
    queryFn: async () => {
      if (!actor) return false;
      return actor.isCallerAdmin();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useGetNotes() {
  const { actor, isFetching } = useActor();
  return useQuery<Note[]>({
    queryKey: ["notes"],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getAllNotes();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useGetVideos() {
  const { actor, isFetching } = useActor();
  return useQuery<YouTubeVideo[]>({
    queryKey: ["videos"],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getAllVideos();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useGetBlogs() {
  const { actor, isFetching } = useActor();
  return useQuery<BlogPost[]>({
    queryKey: ["blogs"],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getAllBlogs();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useCreateNote() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      content: string;
      category: NoteCategory;
    }) => actor!.createNote(data.title, data.content, data.category),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useUpdateNote() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      id: bigint;
      title: string;
      content: string;
      category: NoteCategory;
    }) => actor!.updateNote(data.id, data.title, data.content, data.category),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useDeleteNote() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: bigint) => actor!.deleteNote(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useCreateVideo() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; description: string; url: string }) =>
      actor!.createVideo(data.title, data.description, data.url),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["videos"] }),
  });
}

export function useDeleteVideo() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: bigint) => actor!.deleteVideo(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["videos"] }),
  });
}

export function useCreateBlog() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; content: string; author: string }) =>
      actor!.createBlog(data.title, data.content, data.author),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blogs"] }),
  });
}

export function useUpdateBlog() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      id: bigint;
      title: string;
      content: string;
      author: string;
    }) => actor!.updateBlog(data.id, data.title, data.content, data.author),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blogs"] }),
  });
}

export function useDeleteBlog() {
  const { actor } = useActor();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: bigint) => actor!.deleteBlog(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blogs"] }),
  });
}
