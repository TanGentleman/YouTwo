type VectaraChunk = {
  title: string;
  metadata: {
    sidebar_position: string;
    title: string;
  };
  parts: Array<{
    text: string;
    context: string;
    custom_dimensions: {};
    metadata: {
      breadcrumb?: string[];
      is_title?: boolean;
      title?: string;
      offset: number;
      lang?: string;
      len?: number;
      section?: number;
      title_level?: number;
    };
  }>;
};
