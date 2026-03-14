import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  BookOpen,
  Heart,
  Newspaper,
  Star,
  Users,
  Video,
} from "lucide-react";
import { motion } from "motion/react";

const sections = [
  {
    to: "/notes",
    icon: BookOpen,
    title: "Resource Notes",
    description:
      "Curated notes covering Autism, ADHD, Dyslexia, and more — written by specialists and organized for quick reference.",
    color: "bg-primary/10 text-primary",
    cta: "Browse Notes",
    ocid: "home.notes.link",
  },
  {
    to: "/videos",
    icon: Video,
    title: "YouTube Videos",
    description:
      "A hand-picked library of YouTube videos on SEN strategies, therapy techniques, and real-world classroom approaches.",
    color: "bg-accent/20 text-foreground",
    cta: "Watch Videos",
    ocid: "home.videos.link",
  },
  {
    to: "/blog",
    icon: Newspaper,
    title: "Blog & Articles",
    description:
      "Expert articles and personal stories from educators, therapists, and parents navigating the world of special education.",
    color: "bg-secondary text-secondary-foreground",
    cta: "Read Blog",
    ocid: "home.blog.link",
  },
];

const stats = [
  { icon: BookOpen, value: "50+", label: "Resource Notes" },
  { icon: Video, value: "30+", label: "Curated Videos" },
  { icon: Newspaper, value: "20+", label: "Blog Articles" },
  { icon: Users, value: "1000+", label: "Educators Helped" },
];

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="/assets/generated/sen-hero.dim_1200x480.jpg"
            alt="SEN Learning Hub"
            className="w-full h-full object-cover opacity-20"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background/90 to-secondary/60" />
        </div>

        <div className="relative container mx-auto px-4 py-20 md:py-28">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-2xl"
          >
            <div className="inline-flex items-center gap-2 bg-accent/20 text-foreground px-3 py-1 rounded-full text-sm font-medium mb-5">
              <Star
                className="w-3.5 h-3.5 text-accent-foreground"
                fill="currentColor"
              />
              Special Education Needs Resources
            </div>
            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold leading-tight text-foreground mb-5">
              Every learner deserves to{" "}
              <span className="text-primary">thrive</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
              A comprehensive hub for parents, educators, and therapists.
              Discover notes, videos, and expert articles on Autism, ADHD,
              Dyslexia, and more.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                asChild
                size="lg"
                className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-warm"
                data-ocid="home.explore.button"
              >
                <Link to="/notes">
                  Explore Resources <ArrowRight className="ml-2 w-4 h-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                data-ocid="home.blog.primary_button"
              >
                <Link to="/blog">Read the Blog</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-primary py-10">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center text-primary-foreground"
              >
                <stat.icon className="w-6 h-6 mx-auto mb-1 opacity-70" />
                <div className="font-display text-3xl font-bold">
                  {stat.value}
                </div>
                <div className="text-sm opacity-70">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Section cards */}
      <section className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-3">
            Explore the Hub
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Everything you need to support special education learners, all in
            one place.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {sections.map((section, i) => (
            <motion.div
              key={section.to}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
            >
              <Card className="h-full hover:shadow-card transition-shadow group border-border">
                <CardContent className="p-6 flex flex-col h-full">
                  <div
                    className={`w-12 h-12 rounded-2xl ${section.color} flex items-center justify-center mb-4`}
                  >
                    <section.icon className="w-6 h-6" />
                  </div>
                  <h3 className="font-display text-xl font-semibold text-foreground mb-2">
                    {section.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed flex-1 mb-4">
                    {section.description}
                  </p>
                  <Link
                    to={section.to}
                    data-ocid={section.ocid}
                    className="inline-flex items-center gap-1.5 text-primary text-sm font-medium hover:gap-2.5 transition-all"
                  >
                    {section.cta} <ArrowRight className="w-4 h-4" />
                  </Link>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA banner */}
      <section className="container mx-auto px-4 pb-16">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="bg-secondary rounded-3xl p-10 text-center"
        >
          <Heart className="w-8 h-8 text-primary mx-auto mb-4" />
          <h2 className="font-display text-2xl md:text-3xl font-bold text-foreground mb-3">
            Supporting every learner's journey
          </h2>
          <p className="text-muted-foreground mb-6 max-w-lg mx-auto">
            Whether you're a teacher, parent, or therapist — our resources are
            here to help you make a difference.
          </p>
          <Button
            asChild
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            data-ocid="home.cta.button"
          >
            <Link to="/notes">Get Started Today</Link>
          </Button>
        </motion.div>
      </section>
    </div>
  );
}
