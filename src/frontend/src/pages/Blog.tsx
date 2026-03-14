import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
import {
  Calendar,
  Edit2,
  Loader2,
  Newspaper,
  Plus,
  Trash2,
  User,
  X,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { toast } from "sonner";
import {
  type BlogPost,
  useCreateBlog,
  useDeleteBlog,
  useGetBlogs,
  useIsAdmin,
  useUpdateBlog,
} from "../hooks/useQueries";

function formatDate(created: bigint) {
  const ms = Number(created / BigInt(1_000_000));
  return new Date(ms).toLocaleDateString("en-GB", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

const SAMPLE_BLOGS: BlogPost[] = [
  {
    id: BigInt(1),
    title: "My Journey Teaching a Child with Autism: What I Wish I'd Known",
    content:
      "When I first walked into a classroom with an autistic student, I had good intentions but limited training. Over five years, I learned that the most powerful tool isn't a curriculum or a strategy — it's genuine curiosity about who your student is as an individual.\n\nEvery autistic child is different. Some are incredibly verbal; others communicate through AAC devices or pictures. Some have profound sensory sensitivities; others seem to seek sensory input constantly. The key is observation before intervention.\n\nI learned to create a sensory-friendly corner in my classroom — a small tent with fairy lights and a weighted blanket. It changed everything for one student who would otherwise spend the first hour of every day dysregulated.\n\nWhat I wish I'd known: start with relationship, not remediation. Once a child trusts you, learning becomes possible.",
    author: "Sarah Mitchell, SENCO",
    created: BigInt(Date.now() - 7 * 24 * 60 * 60 * 1000) * BigInt(1_000_000),
  },
  {
    id: BigInt(2),
    title: "ADHD Is Not a Discipline Problem: Reframing Behaviour in Schools",
    content:
      "One of the most damaging myths about ADHD is that children 'choose' to be disruptive. As a school psychologist working with hundreds of families, I've seen how this misconception leads to punitive approaches that make outcomes worse, not better.\n\nADHD is a neurological difference in executive function. A child who blurts out answers isn't being rude — they're managing a brain that moves faster than its brakes. A child who can't sit still isn't being defiant — their nervous system requires movement to regulate attention.\n\nSchools that shift from 'why won't he behave?' to 'what does he need to succeed?' see dramatic improvements. This includes movement breaks, flexible seating, task chunking, and clear visual routines.\n\nThe investment in understanding pays dividends for the whole class, not just the ADHD student.",
    author: "Dr. James Okafor, Educational Psychologist",
    created: BigInt(Date.now() - 14 * 24 * 60 * 60 * 1000) * BigInt(1_000_000),
  },
  {
    id: BigInt(3),
    title: "How We Helped Our Daughter Discover She Was Dyslexic at Age Nine",
    content:
      "For three years, we watched our daughter struggle with reading while being told she was 'just a slow starter' or 'not trying hard enough.' The frustration and shame she carried was heartbreaking.\n\nThe turning point came when her class teacher recommended an assessment. The dyslexia diagnosis didn't feel like a label — it felt like a key. Suddenly, we had language for what she was experiencing, and a roadmap forward.\n\nWe found a specialist reading tutor trained in Orton-Gillingham, switched to audiobooks for pleasure reading, and worked with her school to allow typed assignments. Within a year, her confidence had transformed.\n\nShe's now twelve and dreams of becoming a lawyer. Dyslexia didn't define her ceiling — but finding out about it absolutely changed her trajectory.",
    author: "Emma Thornton, Parent",
    created: BigInt(Date.now() - 21 * 24 * 60 * 60 * 1000) * BigInt(1_000_000),
  },
  {
    id: BigInt(4),
    title: "Building an Inclusive Classroom Culture: Small Changes, Big Impact",
    content:
      "Inclusion isn't a placement — it's a philosophy. After twenty years in primary education, I've come to believe that the most inclusive classrooms aren't defined by the resources they have, but by the attitudes they cultivate.\n\nPractical starting points that cost nothing:\n• Talk openly about different learning styles from the first week of school\n• Celebrate effort and strategy over grades and raw ability\n• Introduce the concept of 'different brains' through picture books from age five\n• Seat students thoughtfully to promote peer support\n\nWhen neurotypical students understand and accept difference from an early age, they become natural allies rather than bystanders. The ripple effects of this cultural work extend far beyond any individual student with SEN.",
    author: "Priya Nair, Primary School Teacher",
    created: BigInt(Date.now() - 28 * 24 * 60 * 60 * 1000) * BigInt(1_000_000),
  },
];

type FormState = { title: string; content: string; author: string };

export default function Blog() {
  const { data: blogsData, isLoading } = useGetBlogs();
  const { data: isAdmin } = useIsAdmin();
  const createBlog = useCreateBlog();
  const updateBlog = useUpdateBlog();
  const deleteBlog = useDeleteBlog();

  const blogs = blogsData && blogsData.length > 0 ? blogsData : SAMPLE_BLOGS;

  const [selectedPost, setSelectedPost] = useState<BlogPost | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
  const [form, setForm] = useState<FormState>({
    title: "",
    content: "",
    author: "",
  });

  function openAdd() {
    setEditingPost(null);
    setForm({ title: "", content: "", author: "" });
    setFormOpen(true);
  }

  function openEdit(post: BlogPost) {
    setEditingPost(post);
    setForm({ title: post.title, content: post.content, author: post.author });
    setFormOpen(true);
  }

  async function handleSubmit() {
    if (!form.title.trim() || !form.content.trim() || !form.author.trim()) {
      toast.error("All fields are required.");
      return;
    }
    try {
      if (editingPost) {
        await updateBlog.mutateAsync({ id: editingPost.id, ...form });
        toast.success("Post updated!");
      } else {
        await createBlog.mutateAsync(form);
        toast.success("Post published!");
      }
      setFormOpen(false);
    } catch {
      toast.error("Something went wrong.");
    }
  }

  async function handleDelete(post: BlogPost) {
    try {
      await deleteBlog.mutateAsync(post.id);
      toast.success("Post deleted.");
    } catch {
      toast.error("Failed to delete post.");
    }
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            Blog & Articles
          </h1>
          <p className="text-muted-foreground mt-1">
            Stories, insights, and expertise from the SEN community
          </p>
        </div>
        {isAdmin && (
          <Button
            onClick={openAdd}
            data-ocid="blog.add.button"
            className="bg-primary text-primary-foreground"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Post
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-5" data-ocid="blog.loading_state">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : blogs.length === 0 ? (
        <div
          className="text-center py-20 text-muted-foreground"
          data-ocid="blog.empty_state"
        >
          <Newspaper className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium">No blog posts yet.</p>
          {isAdmin && (
            <p className="text-sm mt-1">Click "Add Post" to write one.</p>
          )}
        </div>
      ) : (
        <div className="max-w-3xl space-y-6">
          {blogs.map((post, i) => (
            <motion.div
              key={post.id.toString()}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              data-ocid={`blog.item.${i + 1}`}
            >
              <Card
                className="cursor-pointer hover:shadow-card transition-shadow border-border group"
                onClick={() => setSelectedPost(post)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="font-display text-xl font-semibold text-foreground leading-snug group-hover:text-primary transition-colors">
                      {post.title}
                    </h2>
                    {isAdmin && (
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          data-ocid={`blog.edit_button.${i + 1}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            openEdit(post);
                          }}
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          data-ocid={`blog.delete_button.${i + 1}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(post);
                          }}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                    <span className="flex items-center gap-1">
                      <User className="w-3.5 h-3.5" />
                      {post.author}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {formatDate(post.created)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
                    {post.content}
                  </p>
                  <span className="inline-block mt-3 text-xs font-medium text-primary">
                    Read more →
                  </span>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Post detail dialog */}
      <AnimatePresence>
        {selectedPost && (
          <Dialog open onOpenChange={() => setSelectedPost(null)}>
            <DialogContent
              className="max-w-2xl max-h-[85vh] overflow-y-auto"
              data-ocid="blog.dialog"
            >
              <DialogHeader>
                <DialogTitle className="font-display text-xl leading-snug">
                  {selectedPost.title}
                </DialogTitle>
                <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
                  <span className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {selectedPost.author}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(selectedPost.created)}
                  </span>
                </div>
              </DialogHeader>
              <div className="whitespace-pre-wrap text-sm text-muted-foreground leading-relaxed mt-2">
                {selectedPost.content}
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setSelectedPost(null)}
                  data-ocid="blog.close_button"
                >
                  <X className="w-4 h-4 mr-1.5" /> Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>

      {/* Add/Edit dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-lg" data-ocid="blog.modal">
          <DialogHeader>
            <DialogTitle className="font-display">
              {editingPost ? "Edit Post" : "New Blog Post"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label htmlFor="blog-title">Title</Label>
              <Input
                id="blog-title"
                value={form.title}
                onChange={(e) =>
                  setForm((p) => ({ ...p, title: e.target.value }))
                }
                placeholder="Post title…"
                data-ocid="blog.title.input"
              />
            </div>
            <div>
              <Label htmlFor="blog-author">Author</Label>
              <Input
                id="blog-author"
                value={form.author}
                onChange={(e) =>
                  setForm((p) => ({ ...p, author: e.target.value }))
                }
                placeholder="Your name and role…"
                data-ocid="blog.author.input"
              />
            </div>
            <div>
              <Label htmlFor="blog-content">Content</Label>
              <Textarea
                id="blog-content"
                value={form.content}
                onChange={(e) =>
                  setForm((p) => ({ ...p, content: e.target.value }))
                }
                placeholder="Write your blog post…"
                rows={8}
                data-ocid="blog.content.textarea"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setFormOpen(false)}
              data-ocid="blog.cancel_button"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createBlog.isPending || updateBlog.isPending}
              data-ocid="blog.submit_button"
              className="bg-primary text-primary-foreground"
            >
              {(createBlog.isPending || updateBlog.isPending) && (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              )}
              {editingPost ? "Save Changes" : "Publish Post"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
