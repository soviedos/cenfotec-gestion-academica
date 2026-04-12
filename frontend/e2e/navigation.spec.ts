import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("root redirects to /dashboard", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL("/dashboard");
  });

  test("displays the Dashboard page with heading", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  });

  test("evaluacion-docente redirects to inicio", async ({ page }) => {
    await page.goto("/evaluacion-docente");
    await expect(page).toHaveURL("/evaluacion-docente/inicio");
  });

  test("sidebar navigation works for evaluacion-docente sections", async ({
    page,
  }) => {
    await page.goto("/evaluacion-docente/inicio");

    const routes = [
      {
        label: "Carga de PDFs",
        url: "/evaluacion-docente/carga",
        heading: "Cargar PDFs",
      },
      {
        label: "Biblioteca",
        url: "/evaluacion-docente/biblioteca",
        heading: "Biblioteca",
      },
      {
        label: "Docentes",
        url: "/evaluacion-docente/docentes",
        heading: "Docentes",
      },
      {
        label: "Reportes",
        url: "/evaluacion-docente/reportes",
        heading: "Reportes",
      },
    ];

    for (const route of routes) {
      await page.getByRole("link", { name: route.label }).first().click();
      await expect(page).toHaveURL(route.url);
      await expect(
        page.getByRole("heading", { name: route.heading, exact: true }),
      ).toBeVisible();
    }
  });

  test("page has correct document title", async ({ page }) => {
    await page.goto("/evaluacion-docente/carga");
    await expect(page).toHaveTitle(/Cargar PDFs/);
  });
});
