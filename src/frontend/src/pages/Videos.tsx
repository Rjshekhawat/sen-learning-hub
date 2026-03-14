import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, Trash2, Video } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { toast } from "sonner";
import {
  type YouTubeVideo,
  useCreateVideo,
  useDeleteVideo,
  useGetVideos,
  useIsAdmin,
} from "../hooks/useQueries";

function toEmbedUrl(url: string): string {
  try {
    const u = new URL(url);
    let videoId = "";
    if (u.hostname.includes("youtu.be")) {
      videoId = u.pathname.slice(1).split("?")[0];
    } else if (u.hostname.includes("youtube.com")) {
      videoId = u.searchParams.get("v") ?? "";
      if (!videoId && u.pathname.startsWith("/embed/")) {
        return url;
      }
    }
    return videoId ? `https://www.youtube.com/embed/${videoId}` : url;
  } catch {
    return url;
  }
}

const SAMPLE_VIDEOS: YouTubeVideo[] = [
  {
    id: BigInt(1),
    title: "Featured SEN Resource",
    description:
      "A featured video resource for special education needs. Log in as admin to update the title and description.",
    url: "https://youtu.be/UzOkWmKZcI8",
  },
  {
    id: BigInt(2),
    title: "Understanding Autism: A Guide for Teachers",
    description:
      "An essential introduction to autism for classroom educators, covering sensory needs, communication differences, and practical strategies.",
    url: "https://www.youtube.com/watch?v=Lk4qs8jGN4U",
  },
  {
    id: BigInt(3),
    title: "ADHD in Children: What Teachers Need to Know",
    description:
      "This video breaks down how ADHD manifests in learning environments and offers actionable classroom management strategies.",
    url: "https://www.youtube.com/watch?v=nMFWuLTHFoU",
  },
  {
    id: BigInt(4),
    title: "How to Support Students with Dyslexia",
    description:
      "Explore evidence-based reading intervention techniques and classroom accommodations for students with dyslexia.",
    url: "https://www.youtube.com/watch?v=zafiGBrFkRM",
  },
  {
    id: BigInt(5),
    title: "Sensory Processing and Learning",
    description:
      "Learn how sensory processing challenges affect learning and discover occupational therapy strategies to support regulation.",
    url: "https://www.youtube.com/watch?v=3bKuoKNEgKE",
  },
  {
    id: BigInt(6),
    title: "Building Inclusive Classrooms for All Learners",
    description:
      "Practical approaches to Universal Design for Learning (UDL) that benefit every student, including those with SEN.",
    url: "https://www.youtube.com/watch?v=bDvKnY0g6e4",
  },
  {
    id: BigInt(7),
    title: "Supporting Emotional Regulation in SEN Students",
    description:
      "Strategies from child psychology to help students with emotional and behavioural challenges develop self-regulation skills.",
    url: "https://www.youtube.com/watch?v=1ZKqutdMQW0",
  },
];

export default function Videos() {
  const { data: videosData, isLoading } = useGetVideos();
  const { data: isAdmin } = useIsAdmin();
  const createVideo = useCreateVideo();
  const deleteVideo = useDeleteVideo();

  const videos =
    videosData && videosData.length > 0 ? videosData : SAMPLE_VIDEOS;

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", url: "" });

  async function handleSubmit() {
    if (!form.title.trim() || !form.url.trim()) {
      toast.error("Title and URL are required.");
      return;
    }
    try {
      await createVideo.mutateAsync(form);
      toast.success("Video added!");
      setFormOpen(false);
      setForm({ title: "", description: "", url: "" });
    } catch {
      toast.error("Failed to add video.");
    }
  }

  async function handleDelete(video: YouTubeVideo) {
    try {
      await deleteVideo.mutateAsync(video.id);
      toast.success("Video removed.");
    } catch {
      toast.error("Failed to remove video.");
    }
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            YouTube Videos
          </h1>
          <p className="text-muted-foreground mt-1">
            Curated videos on SEN strategies and approaches
          </p>
        </div>
        {isAdmin && (
          <Button
            onClick={() => setFormOpen(true)}
            data-ocid="videos.add.button"
            className="bg-primary text-primary-foreground"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Video
          </Button>
        )}
      </div>

      {isLoading ? (
        <div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
          data-ocid="videos.loading_state"
        >
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div
          className="text-center py-20 text-muted-foreground"
          data-ocid="videos.empty_state"
        >
          <Video className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium">No videos added yet.</p>
          {isAdmin && (
            <p className="text-sm mt-1">Click "Add Video" to get started.</p>
          )}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video, i) => (
            <motion.div
              key={video.id.toString()}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              data-ocid={`videos.item.${i + 1}`}
            >
              <Card className="h-full flex flex-col overflow-hidden border-border hover:shadow-card transition-shadow group">
                <div className="relative bg-muted aspect-video">
                  <iframe
                    src={toEmbedUrl(video.url)}
                    title={video.title}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
                <CardContent className="p-4 flex flex-col flex-1">
                  <h3 className="font-display font-semibold text-foreground text-sm leading-snug mb-1.5 line-clamp-2">
                    {video.title}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3 flex-1">
                    {video.description}
                  </p>
                  {isAdmin && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-3 text-destructive hover:text-destructive hover:bg-destructive/10 self-start opacity-0 group-hover:opacity-100 transition-opacity"
                      data-ocid={`videos.delete_button.${i + 1}`}
                      onClick={() => handleDelete(video)}
                    >
                      <Trash2 className="w-3.5 h-3.5 mr-1" /> Remove
                    </Button>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Add Video dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-md" data-ocid="videos.modal">
          <DialogHeader>
            <DialogTitle className="font-display">
              Add YouTube Video
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label htmlFor="video-title">Title</Label>
              <Input
                id="video-title"
                value={form.title}
                onChange={(e) =>
                  setForm((p) => ({ ...p, title: e.target.value }))
                }
                placeholder="Video title…"
                data-ocid="videos.title.input"
              />
            </div>
            <div>
              <Label htmlFor="video-url">YouTube URL</Label>
              <Input
                id="video-url"
                value={form.url}
                onChange={(e) =>
                  setForm((p) => ({ ...p, url: e.target.value }))
                }
                placeholder="https://www.youtube.com/watch?v=…"
                data-ocid="videos.url.input"
              />
            </div>
            <div>
              <Label htmlFor="video-desc">Description</Label>
              <Textarea
                id="video-desc"
                value={form.description}
                onChange={(e) =>
                  setForm((p) => ({ ...p, description: e.target.value }))
                }
                placeholder="Briefly describe the video…"
                rows={3}
                data-ocid="videos.description.textarea"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setFormOpen(false)}
              data-ocid="videos.cancel_button"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createVideo.isPending}
              data-ocid="videos.submit_button"
              className="bg-primary text-primary-foreground"
            >
              {createVideo.isPending && (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              )}
              Add Video
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
