import { Toaster } from "@/components/ui/sonner";
import {
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import Layout from "./components/Layout";
import Blog from "./pages/Blog";
import Home from "./pages/Home";
import Notes from "./pages/Notes";
import Videos from "./pages/Videos";

const rootRoute = createRootRoute({
  component: () => (
    <Layout>
      <Outlet />
    </Layout>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Home,
});
const notesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/notes",
  component: Notes,
});
const videosRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/videos",
  component: Videos,
});
const blogRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/blog",
  component: Blog,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  notesRoute,
  videosRoute,
  blogRoute,
]);
const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

export default function App() {
  return (
    <>
      <RouterProvider router={router} />
      <Toaster richColors />
    </>
  );
}
