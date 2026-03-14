import Map "mo:core/Map";
import Nat "mo:core/Nat";
import List "mo:core/List";
import Iter "mo:core/Iter";
import Runtime "mo:core/Runtime";
import Principal "mo:core/Principal";
import Time "mo:core/Time";
import MixinAuthorization "authorization/MixinAuthorization";
import AccessControl "authorization/access-control";

actor {
  let accessControlState = AccessControl.initState();
  include MixinAuthorization(accessControlState);

  public type NoteCategory = {
    #autism;
    #adhd;
    #dyslexia;
    #general;
  };

  public type Note = {
    id : Nat;
    title : Text;
    content : Text;
    category : NoteCategory;
    created : Time.Time;
  };

  public type YouTubeVideo = {
    id : Nat;
    title : Text;
    description : Text;
    url : Text;
  };

  public type BlogPost = {
    id : Nat;
    title : Text;
    content : Text;
    author : Text;
    created : Time.Time;
  };

  var nextNoteId = 0;
  var nextVideoId = 0;
  var nextBlogId = 0;

  let notes = Map.empty<Nat, Note>();
  let videos = Map.empty<Nat, YouTubeVideo>();
  let blogs = Map.empty<Nat, BlogPost>();

  module NoteCategory {
    public func toText(category : NoteCategory) : Text {
      switch (category) {
        case (#autism) { "Autism" };
        case (#adhd) { "ADHD" };
        case (#dyslexia) { "Dyslexia" };
        case (#general) { "General" };
      };
    };
  };

  // Notes CRUD
  public shared ({ caller }) func createNote(title : Text, content : Text, category : NoteCategory) : async Note {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can create notes");
    };

    let note : Note = {
      id = nextNoteId;
      title;
      content;
      category;
      created = Time.now();
    };
    notes.add(nextNoteId, note);
    nextNoteId += 1;
    note;
  };

  public query ({ caller }) func getNote(id : Nat) : async ?Note {
    notes.get(id);
  };

  public query ({ caller }) func getAllNotes() : async [Note] {
    notes.values().toArray();
  };

  public query ({ caller }) func getNotesByCategory(category : NoteCategory) : async [Note] {
    let list = List.empty<Note>();
    for ((_, note) in notes.entries()) {
      if (note.category == category) {
        list.add(note);
      };
    };
    list.toArray();
  };

  public shared ({ caller }) func updateNote(id : Nat, title : Text, content : Text, category : NoteCategory) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can update notes");
    };

    switch (notes.get(id)) {
      case (null) {
        Runtime.trap("Note not found");
      };
      case (?existing) {
        let updated : Note = {
          id;
          title;
          content;
          category;
          created = existing.created;
        };
        notes.add(id, updated);
      };
    };
  };

  public shared ({ caller }) func deleteNote(id : Nat) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can delete notes");
    };
    if (not notes.containsKey(id)) {
      Runtime.trap("Note not found");
    };
    notes.remove(id);
  };

  // YouTube Videos CRUD
  public shared ({ caller }) func createVideo(title : Text, description : Text, url : Text) : async YouTubeVideo {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can create videos");
    };

    let video : YouTubeVideo = {
      id = nextVideoId;
      title;
      description;
      url;
    };
    videos.add(nextVideoId, video);
    nextVideoId += 1;
    video;
  };

  public query ({ caller }) func getVideo(id : Nat) : async ?YouTubeVideo {
    videos.get(id);
  };

  public query ({ caller }) func getAllVideos() : async [YouTubeVideo] {
    videos.values().toArray();
  };

  public shared ({ caller }) func updateVideo(id : Nat, title : Text, description : Text, url : Text) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can update videos");
    };

    switch (videos.get(id)) {
      case (null) {
        Runtime.trap("Video not found");
      };
      case (?_) {
        let updated : YouTubeVideo = {
          id;
          title;
          description;
          url;
        };
        videos.add(id, updated);
      };
    };
  };

  public shared ({ caller }) func deleteVideo(id : Nat) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can delete videos");
    };
    if (not videos.containsKey(id)) {
      Runtime.trap("Video not found");
    };
    videos.remove(id);
  };

  // Blog Posts CRUD
  public shared ({ caller }) func createBlog(title : Text, content : Text, author : Text) : async BlogPost {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can create blog posts");
    };

    let blog : BlogPost = {
      id = nextBlogId;
      title;
      content;
      author;
      created = Time.now();
    };
    blogs.add(nextBlogId, blog);
    nextBlogId += 1;
    blog;
  };

  public query ({ caller }) func getBlog(id : Nat) : async ?BlogPost {
    blogs.get(id);
  };

  public query ({ caller }) func getAllBlogs() : async [BlogPost] {
    blogs.values().toArray();
  };

  public shared ({ caller }) func updateBlog(id : Nat, title : Text, content : Text, author : Text) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can update blog posts");
    };

    switch (blogs.get(id)) {
      case (null) {
        Runtime.trap("Blog post not found");
      };
      case (?existing) {
        let updated : BlogPost = {
          id;
          title;
          content;
          author;
          created = existing.created;
        };
        blogs.add(id, updated);
      };
    };
  };

  public shared ({ caller }) func deleteBlog(id : Nat) : async () {
    if (not AccessControl.isAdmin(accessControlState, caller)) {
      Runtime.trap("Unauthorized: Only admins can delete blog posts");
    };
    if (not blogs.containsKey(id)) {
      Runtime.trap("Blog post not found");
    };
    blogs.remove(id);
  };
};
