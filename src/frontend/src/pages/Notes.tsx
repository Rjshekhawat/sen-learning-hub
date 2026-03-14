import { Badge } from "@/components/ui/badge";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { BookOpen, Edit2, Loader2, Plus, Trash2, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { toast } from "sonner";
import {
  type Note,
  NoteCategory,
  useCreateNote,
  useDeleteNote,
  useGetNotes,
  useIsAdmin,
  useUpdateNote,
} from "../hooks/useQueries";

const CATEGORIES: { value: string; label: string; color: string }[] = [
  { value: "all", label: "All", color: "" },
  {
    value: NoteCategory.autism,
    label: "Autism",
    color: "bg-blue-100 text-blue-800",
  },
  {
    value: NoteCategory.adhd,
    label: "ADHD",
    color: "bg-orange-100 text-orange-800",
  },
  {
    value: NoteCategory.dyslexia,
    label: "Dyslexia",
    color: "bg-purple-100 text-purple-800",
  },
  {
    value: NoteCategory.general,
    label: "General",
    color: "bg-green-100 text-green-800",
  },
];

function getCategoryStyle(cat: NoteCategory) {
  return CATEGORIES.find((c) => c.value === cat)?.color ?? "";
}
function getCategoryLabel(cat: NoteCategory) {
  return CATEGORIES.find((c) => c.value === cat)?.label ?? cat;
}

const SAMPLE_NOTES: Note[] = [
  {
    id: BigInt(1),
    title: "Understanding Autism Spectrum Disorder in the Classroom",
    content:
      "Autism Spectrum Disorder (ASD) is a neurodevelopmental condition characterized by differences in social communication, sensory processing, and behavior. In classroom settings, educators can support autistic learners by providing clear visual schedules, minimizing sensory overload, offering predictable routines, and using visual supports alongside verbal instructions.\n\nKey strategies include:\n• Use of social stories to prepare for transitions\n• Sensory breaks and quiet zones\n• Clear, concrete language and instructions\n• Peer buddy systems for social integration",
    category: NoteCategory.autism,
    created: BigInt(Date.now()) * BigInt(1_000_000),
  },
  {
    id: BigInt(2),
    title: "ADHD: Executive Function Strategies for Students",
    content:
      "Students with ADHD often struggle with executive function skills including working memory, impulse control, and task initiation. Structured environments and explicit strategy instruction are critical for academic success.\n\nEffective classroom accommodations:\n• Break tasks into smaller, manageable steps\n• Use visual timers for task transitions\n• Provide frequent, specific positive reinforcement\n• Allow movement breaks between seated tasks\n• Use graphic organizers for writing assignments",
    category: NoteCategory.adhd,
    created: BigInt(Date.now()) * BigInt(1_000_000),
  },
  {
    id: BigInt(3),
    title: "Dyslexia: Multi-Sensory Reading Approaches",
    content:
      "Dyslexia is a specific learning disability that affects reading fluency and decoding. The Orton-Gillingham approach and its derivatives have strong evidence for supporting dyslexic readers through structured, sequential, multi-sensory instruction.\n\nCore principles:\n• Phonological awareness training\n• Explicit phonics instruction (letter-sound relationships)\n• Kinesthetic activities (sand trays, textured letters)\n• Extended time for reading and writing tasks\n• Text-to-speech technology support",
    category: NoteCategory.dyslexia,
    created: BigInt(Date.now()) * BigInt(1_000_000),
  },
  {
    id: BigInt(4),
    title: "Communicating with Parents of SEN Students",
    content:
      "Effective home-school collaboration is essential for SEN student success. Regular, structured communication helps parents understand their child's progress and how to reinforce strategies at home.\n\nBest practices:\n• Weekly communication logs or home-school diaries\n• Scheduled review meetings with clear agendas\n• Celebrating small wins alongside challenges\n• Providing parents with practical strategies to use at home\n• Using plain language and avoiding jargon",
    category: NoteCategory.general,
    created: BigInt(Date.now()) * BigInt(1_000_000),
  },
];

type FormState = {
  title: string;
  content: string;
  category: NoteCategory;
};

export default function Notes() {
  const { data: notesData, isLoading } = useGetNotes();
  const { data: isAdmin } = useIsAdmin();
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();

  const notes = notesData && notesData.length > 0 ? notesData : SAMPLE_NOTES;

  const [activeCategory, setActiveCategory] = useState("all");
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [form, setForm] = useState<FormState>({
    title: "",
    content: "",
    category: NoteCategory.general,
  });

  const filtered =
    activeCategory === "all"
      ? notes
      : notes.filter((n) => n.category === activeCategory);

  function openAdd() {
    setEditingNote(null);
    setForm({ title: "", content: "", category: NoteCategory.general });
    setFormOpen(true);
  }

  function openEdit(note: Note) {
    setEditingNote(note);
    setForm({
      title: note.title,
      content: note.content,
      category: note.category,
    });
    setFormOpen(true);
  }

  async function handleSubmit() {
    if (!form.title.trim() || !form.content.trim()) {
      toast.error("Title and content are required.");
      return;
    }
    try {
      if (editingNote) {
        await updateNote.mutateAsync({ id: editingNote.id, ...form });
        toast.success("Note updated!");
      } else {
        await createNote.mutateAsync(form);
        toast.success("Note created!");
      }
      setFormOpen(false);
    } catch {
      toast.error("Something went wrong.");
    }
  }

  async function handleDelete(note: Note) {
    try {
      await deleteNote.mutateAsync(note.id);
      toast.success("Note deleted.");
    } catch {
      toast.error("Failed to delete note.");
    }
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            Resource Notes
          </h1>
          <p className="text-muted-foreground mt-1">
            Expert notes on special education topics
          </p>
        </div>
        {isAdmin && (
          <Button
            onClick={openAdd}
            data-ocid="notes.add.button"
            className="bg-primary text-primary-foreground"
          >
            <Plus className="w-4 h-4 mr-1.5" /> Add Note
          </Button>
        )}
      </div>

      <Tabs
        value={activeCategory}
        onValueChange={setActiveCategory}
        className="mb-8"
      >
        <TabsList className="bg-secondary">
          {CATEGORIES.map((cat) => (
            <TabsTrigger
              key={cat.value}
              value={cat.value}
              data-ocid={`notes.${cat.value}.tab`}
            >
              {cat.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-5"
          data-ocid="notes.loading_state"
        >
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div
          className="text-center py-20 text-muted-foreground"
          data-ocid="notes.empty_state"
        >
          <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="font-medium">No notes in this category yet.</p>
          {isAdmin && (
            <p className="text-sm mt-1">Click "Add Note" to create one.</p>
          )}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((note, i) => (
            <motion.div
              key={note.id.toString()}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              data-ocid={`notes.item.${i + 1}`}
            >
              <Card
                className="h-full flex flex-col cursor-pointer hover:shadow-card transition-shadow border-border group"
                onClick={() => setSelectedNote(note)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <Badge
                      className={`text-xs ${getCategoryStyle(note.category)}`}
                    >
                      {getCategoryLabel(note.category)}
                    </Badge>
                    {isAdmin && (
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          data-ocid={`notes.edit_button.${i + 1}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            openEdit(note);
                          }}
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          data-ocid={`notes.delete_button.${i + 1}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(note);
                          }}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <h3 className="font-display font-semibold text-foreground leading-snug">
                    {note.title}
                  </h3>
                </CardHeader>
                <CardContent className="flex-1">
                  <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                    {note.content}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Note detail dialog */}
      <AnimatePresence>
        {selectedNote && (
          <Dialog open onOpenChange={() => setSelectedNote(null)}>
            <DialogContent
              className="max-w-2xl max-h-[80vh] overflow-y-auto"
              data-ocid="notes.dialog"
            >
              <DialogHeader>
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={getCategoryStyle(selectedNote.category)}>
                    {getCategoryLabel(selectedNote.category)}
                  </Badge>
                </div>
                <DialogTitle className="font-display text-xl">
                  {selectedNote.title}
                </DialogTitle>
              </DialogHeader>
              <div className="whitespace-pre-wrap text-sm text-muted-foreground leading-relaxed mt-2">
                {selectedNote.content}
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setSelectedNote(null)}
                  data-ocid="notes.close_button"
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
        <DialogContent className="max-w-lg" data-ocid="notes.modal">
          <DialogHeader>
            <DialogTitle className="font-display">
              {editingNote ? "Edit Note" : "Add Note"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label htmlFor="note-title">Title</Label>
              <Input
                id="note-title"
                value={form.title}
                onChange={(e) =>
                  setForm((p) => ({ ...p, title: e.target.value }))
                }
                placeholder="Note title…"
                data-ocid="notes.title.input"
              />
            </div>
            <div>
              <Label htmlFor="note-category">Category</Label>
              <Select
                value={form.category}
                onValueChange={(v) =>
                  setForm((p) => ({ ...p, category: v as NoteCategory }))
                }
              >
                <SelectTrigger data-ocid="notes.category.select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.filter((c) => c.value !== "all").map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="note-content">Content</Label>
              <Textarea
                id="note-content"
                value={form.content}
                onChange={(e) =>
                  setForm((p) => ({ ...p, content: e.target.value }))
                }
                placeholder="Write the note content…"
                rows={6}
                data-ocid="notes.content.textarea"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setFormOpen(false)}
              data-ocid="notes.cancel_button"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createNote.isPending || updateNote.isPending}
              data-ocid="notes.save_button"
              className="bg-primary text-primary-foreground"
            >
              {(createNote.isPending || updateNote.isPending) && (
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
              )}
              {editingNote ? "Save Changes" : "Create Note"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
